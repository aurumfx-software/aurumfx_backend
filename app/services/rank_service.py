from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import (
    User,
    Investment,
    RankCondition,
    RankSetting,
    UserRankHistory,
    Wallet,
    WalletTransaction,
)


# ==========================================================
# SELF LOTS
# ==========================================================

def get_self_lots(
    db: Session,
    user_id: int
):
    """
    Get total ACTIVE + APPROVED investment lots
    directly owned by the user.

    Only ACTIVE + APPROVED investments count
    for rank qualification.
    """

    total_lots = (
        db.query(
            func.coalesce(
                func.sum(Investment.lots),
                0
            )
        )
        .filter(
            Investment.user_id == user_id,

            # ----------------------------------------------
            # ONLY ACTIVE INVESTMENTS
            # ----------------------------------------------

            Investment.investment_status == "ACTIVE",

            # ----------------------------------------------
            # ONLY APPROVED INVESTMENTS
            # ----------------------------------------------

            Investment.approval_status == "APPROVED"
        )
        .scalar()
    )

    return int(total_lots or 0)


# ==========================================================
# TEAM LOTS
# ==========================================================

def get_team_lots(
    db: Session,
    user: User
):
    """
    Get complete team lots.

    Includes:

        User's own ACTIVE + APPROVED lots
        +
        Direct children
        +
        Their children
        +
        Complete recursive downline

    Example:

        FX009
        |
        +-- FX016
        |   +-- A
        |   |   +-- B
        |   |
        |   +-- C
        |
        +-- FX014
        |
        +-- FX015

    Team lots for FX009 include all ACTIVE +
    APPROVED investments in the complete tree.
    """

    # ------------------------------------------------------
    # USER'S OWN ACTIVE LOTS
    # ------------------------------------------------------

    total = get_self_lots(
        db,
        user.id
    )

    # ------------------------------------------------------
    # GET DIRECT CHILDREN
    # ------------------------------------------------------

    children = (
        db.query(User)
        .filter(
            User.enroller_id == user.user_id
        )
        .all()
    )

    # ------------------------------------------------------
    # RECURSIVE DOWNLINE
    # ------------------------------------------------------

    for child in children:

        total += get_team_lots(
            db,
            child
        )

    return int(total)


# ==========================================================
# DIRECT SPONSOR GROUP LOTS
# ==========================================================

def get_direct_sponsor_group_lots(
    db: Session,
    user: User
):
    """
    Get ACTIVE direct sponsors only.

    A direct sponsor is counted only when
    that sponsor personally has at least one
    ACTIVE + APPROVED investment.

    Group lots include:
        sponsor's own ACTIVE + APPROVED lots
        +
        complete recursive downline
    """

    directs = (
        db.query(User)
        .filter(
            User.enroller_id == user.user_id
        )
        .all()
    )

    group_lots = []

    for sponsor in directs:

        # --------------------------------------------------
        # Sponsor's OWN active lots
        # --------------------------------------------------

        sponsor_self_lots = get_self_lots(
            db,
            sponsor.id
        )

        # --------------------------------------------------
        # IMPORTANT:
        # Direct sponsor only counts if
        # THEY personally have active investment
        # --------------------------------------------------

        if sponsor_self_lots <= 0:

            print("--------------------------------")
            print(
                "DIRECT SPONSOR NOT ACTIVE:",
                sponsor.user_id
            )
            print(
                "Own Active Lots:",
                sponsor_self_lots
            )
            print("--------------------------------")

            continue

        # --------------------------------------------------
        # Complete group
        # --------------------------------------------------

        total_group_lots = get_team_lots(
            db,
            sponsor
        )

        group_lots.append(
            int(total_group_lots)
        )

        print("--------------------------------")
        print(
            "ACTIVE DIRECT SPONSOR:",
            sponsor.user_id
        )
        print(
            "Sponsor Own Active Lots:",
            sponsor_self_lots
        )
        print(
            "Complete Group Active Lots:",
            total_group_lots
        )
        print("--------------------------------")

    group_lots.sort(reverse=True)

    return group_lots

# ==========================================================
# CHECK RANK CONDITIONS
# ==========================================================

def check_rank_conditions(
    db: Session,
    rank: RankSetting,
    group_lots: list[int]
):
    """
    Check custom group conditions for a rank.

    Example:

        minimum_group_lots = 50
        required_group_count = 1

    Means:

        At least ONE direct sponsor group
        must contain 50 or more ACTIVE +
        APPROVED lots.

    Another example:

        condition 1:
            50 lots
            2 groups

        condition 2:
            100 lots
            1 group

    The same sponsor group cannot be reused
    for multiple conditions.
    """

    # ------------------------------------------------------
    # COPY GROUP LOTS
    # ------------------------------------------------------

    remaining_groups = group_lots.copy()

    # ------------------------------------------------------
    # GET CONDITIONS
    # ------------------------------------------------------

    conditions = (
        db.query(RankCondition)
        .filter(
            RankCondition.rank_id == rank.id
        )
        .order_by(
            RankCondition.order_no
        )
        .all()
    )

    # ------------------------------------------------------
    # NO CUSTOM CONDITIONS
    # ------------------------------------------------------

    if not conditions:

        print(
            "No custom rank conditions."
        )

        return True

    # ------------------------------------------------------
    # CHECK EACH CONDITION
    # ------------------------------------------------------

    for condition in conditions:

        minimum_group_lots = int(
            condition.minimum_group_lots or 0
        )

        required_group_count = int(
            condition.required_group_count or 0
        )

        # --------------------------------------------------
        # FIND MATCHING GROUPS
        # --------------------------------------------------

        matched = []

        for lots in remaining_groups:

            if lots >= minimum_group_lots:

                matched.append(
                    lots
                )

        # --------------------------------------------------
        # LOG CONDITION
        # --------------------------------------------------

        print("--------------------------------")
        print(
            "Checking Rank Condition"
        )

        print(
            "Rank:",
            rank.rank_name
        )

        print(
            "Minimum Group Lots:",
            minimum_group_lots
        )

        print(
            "Required Group Count:",
            required_group_count
        )

        print(
            "All Groups:",
            group_lots
        )

        print(
            "Matching Groups:",
            matched
        )

        # --------------------------------------------------
        # NOT ENOUGH GROUPS
        # --------------------------------------------------

        if len(matched) < required_group_count:

            print(
                "RANK CONDITION FAILED"
            )

            print(
                "Required:",
                required_group_count
            )

            print(
                "Available:",
                len(matched)
            )

            print("--------------------------------")

            return False

        # --------------------------------------------------
        # HIGHEST GROUPS FIRST
        # --------------------------------------------------

        matched.sort(
            reverse=True
        )

        selected = matched[
            :required_group_count
        ]

        # --------------------------------------------------
        # REMOVE SELECTED GROUPS
        #
        # This prevents one group from being
        # reused for another condition.
        # --------------------------------------------------

        for value in selected:

            remaining_groups.remove(
                value
            )

        print(
            "Condition PASSED"
        )

        print(
            "Selected Groups:",
            selected
        )

        print("--------------------------------")

    # ------------------------------------------------------
    # ALL CONDITIONS PASSED
    # ------------------------------------------------------

    print(
        "ALL RANK CONDITIONS PASSED:",
        rank.rank_name
    )

    return True


# ==========================================================
# GET HIGHEST QUALIFIED RANK
# ==========================================================

def get_highest_qualified_rank(
    db: Session,
    user: User
):
    """
    Find the highest rank currently qualified
    by the user.

    Rank requirements:

        1. Minimum total ACTIVE + APPROVED lots
        2. Minimum direct sponsors
        3. Custom direct sponsor group conditions
    """

    print("")
    print("--------------------------------")
    print(
        "Checking Rank For:",
        user.user_id
    )
    print("--------------------------------")

    # ======================================================
    # TOTAL TEAM LOTS
    # ======================================================

    total_lots = get_team_lots(
        db,
        user
    )

    # ======================================================
    # DIRECT SPONSOR GROUP LOTS
    # ======================================================

    group_lots = get_direct_sponsor_group_lots(
        db,
        user
    )

    # ======================================================
    # LOG SUMMARY
    # ======================================================

    print("")
    print("================================")
    print("RANK CALCULATION")
    print("================================")

    print(
        "User:",
        user.user_id
    )

    print(
        "Total Active Team Lots:",
        total_lots
    )

    print(
        "Direct Sponsor Group Lots:",
        group_lots
    )

    print(
        "Direct Sponsor Count:",
        len(group_lots)
    )

    print("================================")

    # ======================================================
    # GET ACTIVE RANKS
    #
    # HIGHEST RANK FIRST
    # ======================================================

    ranks = (
        db.query(RankSetting)
        .filter(
            RankSetting.status == True
        )
        .order_by(
            RankSetting.rank_no.desc()
        )
        .all()
    )

    # ======================================================
    # CHECK EACH RANK
    # ======================================================

    for rank in ranks:

        print("")
        print("================================")
        print(
            "Checking Rank:",
            rank.rank_name
        )
        print(
            "Rank No:",
            rank.rank_no
        )
        print("================================")

        # ==================================================
        # 1. MINIMUM TOTAL LOTS
        # ==================================================

        minimum_total_lots = int(
            rank.minimum_total_lots or 0
        )

        print(
            "Minimum Total Lots Required:",
            minimum_total_lots
        )

        print(
            "Actual Total Active Lots:",
            total_lots
        )

        if total_lots < minimum_total_lots:

            print(
                "FAILED: Minimum Total Lots"
            )

            continue

        print(
            "PASSED: Minimum Total Lots"
        )

        # ==================================================
        # 2. MINIMUM DIRECT SPONSORS
        # ==================================================

        minimum_direct_sponsors = int(
            rank.minimum_direct_sponsors or 0
        )

        print(
            "Minimum Direct Sponsors Required:",
            minimum_direct_sponsors
        )

        print(
            "Actual Direct Sponsors:",
            len(group_lots)
        )

        if len(group_lots) < minimum_direct_sponsors:

            print(
                "FAILED: Minimum Direct Sponsors"
            )

            continue

        print(
            "PASSED: Minimum Direct Sponsors"
        )

        # ==================================================
        # 3. CUSTOM GROUP CONDITIONS
        # ==================================================

        conditions_passed = check_rank_conditions(
            db,
            rank,
            group_lots
        )

        if not conditions_passed:

            print(
                "FAILED: Custom Rank Conditions"
            )

            continue

        # ==================================================
        # RANK QUALIFIED
        # ==================================================

        print("")
        print("================================")
        print(
            "QUALIFIED:",
            rank.rank_name
        )
        print("================================")

        return rank

    # ======================================================
    # NO RANK QUALIFIED
    # ======================================================

    print("")
    print("--------------------------------")
    print(
        "NO RANK QUALIFIED FOR:",
        user.user_id
    )
    print("--------------------------------")

    return None


# ==========================================================
# ASSIGN RANK
# ==========================================================

def assign_rank(
    db: Session,
    user: User,
    rank: RankSetting
):
    """
    Assign the qualified rank.

    A user cannot receive the same rank twice.

    Rank reward is initially PENDING.
    """

    # ======================================================
    # CHECK EXISTING RANK HISTORY
    # ======================================================

    existing = (
        db.query(UserRankHistory)
        .filter(
            UserRankHistory.user_id == user.id,
            UserRankHistory.rank_id == rank.id
        )
        .first()
    )

    if existing:

        print("")
        print("--------------------------------")
        print(
            "RANK ALREADY ASSIGNED:",
            rank.rank_name
        )
        print(
            "User:",
            user.user_id
        )
        print("--------------------------------")

        return None

    # ======================================================
    # UPDATE CURRENT RANK
    # ======================================================

    user.current_rank_id = rank.id

    # ======================================================
    # GET REWARD
    # ======================================================

    reward_amount = float(
        rank.reward_income or 0
    )

    # ======================================================
    # CREATE RANK HISTORY
    # ======================================================

    history = UserRankHistory(
        user_id=user.id,

        rank_id=rank.id,

        reward_income=reward_amount,

        reward_paid=False,

        paid_at=None
    )

    db.add(history)

    db.flush()

    # ======================================================
    # LOG
    # ======================================================

    print("")
    print("--------------------------------")
    print("RANK ASSIGNED")
    print("--------------------------------")

    print(
        "User:",
        user.user_id
    )

    print(
        "Rank:",
        rank.rank_name
    )

    print(
        "Rank ID:",
        rank.id
    )

    print(
        "Reward:",
        reward_amount
    )

    print(
        "Reward Status:",
        "PENDING"
    )

    print("--------------------------------")

    return history


# ==========================================================
# CREDIT RANK REWARD AS PENDING
# ==========================================================

def credit_rank_reward(
    db: Session,
    history: UserRankHistory
):
    """
    Credit rank reward to wallet.pending_balance.

    IMPORTANT:

        wallet.balance
            = available/paid balance

        wallet.pending_balance
            = generated but not yet paid

    Rank reward is NOT added to wallet.balance.

    Admin fee is NOT deducted here.

    Admin fee is deducted later during payout.
    """

    # ======================================================
    # CHECK ALREADY PAID
    # ======================================================

    if history.reward_paid:

        print(
            "Rank reward already paid:",
            history.id
        )

        return history

    # ======================================================
    # GET REWARD AMOUNT
    # ======================================================

    reward_amount = float(
        history.reward_income or 0
    )

    if reward_amount <= 0:

        print(
            "Rank reward is zero:",
            history.id
        )

        return history

    # ======================================================
    # GET USER WALLET
    # ======================================================

    wallet = (
        db.query(Wallet)
        .filter(
            Wallet.user_id == history.user_id
        )
        .first()
    )

    # ======================================================
    # CREATE WALLET IF MISSING
    # ======================================================

    if not wallet:

        wallet = Wallet(
            user_id=history.user_id,

            balance=0,

            pending_balance=0,

            admin_fee=0
        )

        db.add(wallet)

        db.flush()

    # ======================================================
    # CURRENT VALUES
    # ======================================================

    wallet_balance_before = float(
        wallet.balance or 0
    )

    pending_before = float(
        wallet.pending_balance or 0
    )

    # ======================================================
    # ADD REWARD TO PENDING BALANCE
    # ======================================================

    wallet.pending_balance = (
        pending_before
        + reward_amount
    )

    # ======================================================
    # CREATE WALLET TRANSACTION
    # ======================================================

    transaction = WalletTransaction(
        wallet_id=wallet.id,

        investment_id=None,

        amount=reward_amount,

        transaction_type="RANK_REWARD",

        status="PENDING",

        remarks=(
            f"Pending Rank Reward "
            f"for Rank ID {history.rank_id}"
        )
    )

    db.add(transaction)

    # ======================================================
    # KEEP HISTORY PENDING
    # ======================================================

    history.reward_paid = False

    history.paid_at = None

    db.flush()

    # ======================================================
    # LOG
    # ======================================================

    print("")
    print("--------------------------------")
    print("RANK REWARD")
    print("--------------------------------")

    print(
        "User ID:",
        history.user_id
    )

    print(
        "Rank ID:",
        history.rank_id
    )

    print(
        "Reward:",
        reward_amount
    )

    print(
        "Wallet Balance Before:",
        wallet_balance_before
    )

    print(
        "Wallet Balance After:",
        wallet.balance
    )

    print(
        "Pending Balance Before:",
        pending_before
    )

    print(
        "Pending Balance After:",
        wallet.pending_balance
    )

    print(
        "Transaction Status:",
        "PENDING"
    )

    print(
        "Rank Status:",
        "PENDING"
    )

    print(
        "Admin Fee:",
        "NOT DEDUCTED"
    )

    print("--------------------------------")

    return history


# ==========================================================
# CHECK AND ASSIGN RANK
# ==========================================================

def check_and_assign_rank(
    db: Session,
    user: User
):
    """
    Complete rank qualification flow.

    Steps:

        1. User must have ACTIVE + APPROVED investment.
        2. Calculate total ACTIVE + APPROVED team lots.
        3. Calculate direct sponsor groups.
        4. Check rank requirements.
        5. Assign highest qualified rank.
        6. Create pending rank reward.
        7. Add reward to wallet.pending_balance.
        8. Create pending wallet transaction.
    """

    print("")
    print("==========================================")
    print("CHECK AND ASSIGN RANK")
    print(
        "User:",
        user.user_id
    )
    print("==========================================")

    try:

        # ==================================================
        # 1. CHECK USER'S OWN ACTIVE INVESTMENT
        # ==================================================

        active_investment = (
            db.query(Investment)
            .filter(
                Investment.user_id == user.id,

                Investment.investment_status == "ACTIVE",

                Investment.approval_status == "APPROVED"
            )
            .first()
        )

        # --------------------------------------------------
        # USER DOES NOT HAVE ACTIVE INVESTMENT
        # --------------------------------------------------

        if not active_investment:

            print("")
            print(
                "NO ACTIVE + APPROVED INVESTMENT"
            )

            print(
                "Rank process skipped for:",
                user.user_id
            )

            return None

        print(
            "Active Investment Found:",
            active_investment.id
        )

        # ==================================================
        # 2. FIND HIGHEST QUALIFIED RANK
        # ==================================================

        rank = get_highest_qualified_rank(
            db,
            user
        )

        # --------------------------------------------------
        # NO QUALIFIED RANK
        # --------------------------------------------------

        if not rank:

            print("")
            print(
                "NO QUALIFIED RANK"
            )

            print(
                "User:",
                user.user_id
            )

            return None

        print("")
        print(
            "Qualified Rank:",
            rank.rank_name
        )

        # ==================================================
        # 3. ASSIGN RANK
        # ==================================================

        history = assign_rank(
            db,
            user,
            rank
        )

        # --------------------------------------------------
        # RANK ALREADY EXISTS
        # --------------------------------------------------

        if not history:

            print(
                "Rank was not newly assigned."
            )

            return None

        # ==================================================
        # 4. CREDIT RANK REWARD
        # ==================================================

        credit_rank_reward(
            db,
            history
        )

        # ==================================================
        # 5. COMMIT
        # ==================================================

        db.commit()

        # ==================================================
        # 6. REFRESH HISTORY
        # ==================================================

        db.refresh(history)

        # ==================================================
        # FINAL LOG
        # ==================================================

        print("")
        print("==========================================")
        print(
            "RANK PROCESS COMPLETED SUCCESSFULLY"
        )
        print("==========================================")

        print(
            "User:",
            user.user_id
        )

        print(
            "Rank:",
            rank.rank_name
        )

        print(
            "Rank ID:",
            rank.id
        )

        print(
            "Reward:",
            history.reward_income
        )

        print(
            "Reward Status:",
            "PENDING"
        )

        print("==========================================")

        return history

    except Exception as e:

        # ==================================================
        # ROLLBACK
        # ==================================================

        db.rollback()

        print("")
        print("--------------------------------")
        print(
            "RANK PROCESS FAILED:",
            str(e)
        )
        print("--------------------------------")

        raise