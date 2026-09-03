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

    IMPORTANT:
        Only ACTIVE investments are counted.
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

            # IMPORTANT:
            # Only ACTIVE investments count
            Investment.investment_status == "ACTIVE",

            # Only APPROVED investments count
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
    

    # ------------------------------------------------------
    # SELF LOTS
    # ------------------------------------------------------

    total = get_self_lots(
        db,
        user.id
    )

    # ------------------------------------------------------
    # DIRECT CHILDREN
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
    
    # ------------------------------------------------------
    # GET DIRECT SPONSORS
    # ------------------------------------------------------

    directs = (
        db.query(User)
        .filter(
            User.enroller_id == user.user_id
        )
        .all()
    )

    group_lots = []

    # ------------------------------------------------------
    # CALCULATE EACH COMPLETE GROUP
    # ------------------------------------------------------

    for sponsor in directs:

        lots = get_team_lots(
            db,
            sponsor
        )

        group_lots.append(
            int(lots)
        )

        print("------------------------------------------")
        print(
            "Direct Sponsor:",
            sponsor.user_id
        )
        print(
            "Group Lots:",
            lots
        )
        print("------------------------------------------")

    # ------------------------------------------------------
    # HIGHEST GROUP FIRST
    # ------------------------------------------------------

    group_lots.sort(
        reverse=True
    )

    return group_lots


# ==========================================================
# CHECK RANK CONDITIONS
# ==========================================================

def check_rank_conditions(
    db: Session,
    rank: RankSetting,
    group_lots: list[int]
):
    
    # ------------------------------------------------------
    # COPY GROUP LOTS
    # ------------------------------------------------------

    remaining_groups = group_lots.copy()

    # ------------------------------------------------------
    # GET RANK CONDITIONS
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

        return True

    # ------------------------------------------------------
    # CHECK EACH CONDITION
    # ------------------------------------------------------

    for condition in conditions:

        matched = []

        # --------------------------------------------------
        # FIND GROUPS THAT SATISFY CONDITION
        # --------------------------------------------------

        for lots in remaining_groups:

            if (
                lots
                >= condition.minimum_group_lots
            ):

                matched.append(
                    lots
                )

        # --------------------------------------------------
        # NOT ENOUGH GROUPS
        # --------------------------------------------------

        if (
            len(matched)
            < condition.required_group_count
        ):

            print("--------------------------------")
            print(
                "RANK CONDITION FAILED"
            )

            print(
                "Rank:",
                rank.rank_name
            )

            print(
                "Required Group Lots:",
                condition.minimum_group_lots
            )

            print(
                "Required Group Count:",
                condition.required_group_count
            )

            print(
                "Available Matching Groups:",
                matched
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
            :condition.required_group_count
        ]

        # --------------------------------------------------
        # REMOVE SELECTED GROUPS
        # --------------------------------------------------

        for value in selected:

            remaining_groups.remove(
                value
            )

    # ------------------------------------------------------
    # ALL CONDITIONS PASSED
    # ------------------------------------------------------

    return True


# ==========================================================
# GET HIGHEST QUALIFIED RANK
# ==========================================================

def get_highest_qualified_rank(
    db: Session,
    user: User
):
    
    print("--------------------------------")
    print(
        "Checking Rank For:",
        user.user_id
    )
    print("--------------------------------")

    # ------------------------------------------------------
    # TOTAL TEAM LOTS
    #
    # Includes:
    #
    #   Own lots
    #   +
    #   Complete downline
    # ------------------------------------------------------

    total_lots = get_team_lots(
        db,
        user
    )

    # ------------------------------------------------------
    # DIRECT SPONSOR GROUP LOTS
    #
    # Each direct sponsor gets a separate group.
    # ------------------------------------------------------

    group_lots = (
        get_direct_sponsor_group_lots(
            db,
            user
        )
    )

    print(
        "Total Team Lots:",
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

    # ------------------------------------------------------
    # GET ACTIVE RANKS
    #
    # HIGHEST RANK FIRST
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # CHECK EACH RANK
    # ------------------------------------------------------

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

        # --------------------------------------------------
        # MINIMUM TOTAL LOTS
        # --------------------------------------------------

        minimum_total_lots = int(
            rank.minimum_total_lots or 0
        )

        if (
            total_lots
            < minimum_total_lots
        ):

            print(
                "FAILED: Minimum Total Lots"
            )

            print(
                "Required:",
                minimum_total_lots
            )

            print(
                "Actual:",
                total_lots
            )

            continue

        print(
            "PASSED: Minimum Total Lots"
        )

        # --------------------------------------------------
        # MINIMUM DIRECT SPONSORS
        # --------------------------------------------------

        minimum_direct_sponsors = int(
            rank.minimum_direct_sponsors or 0
        )

        if (
            len(group_lots)
            < minimum_direct_sponsors
        ):

            print(
                "FAILED: Minimum Direct Sponsors"
            )

            print(
                "Required:",
                minimum_direct_sponsors
            )

            print(
                "Actual:",
                len(group_lots)
            )

            continue

        print(
            "PASSED: Minimum Direct Sponsors"
        )

        # --------------------------------------------------
        # CUSTOM GROUP CONDITIONS
        # --------------------------------------------------

        conditions_passed = (
            check_rank_conditions(
                db,
                rank,
                group_lots
            )
        )

        if not conditions_passed:

            print(
                "FAILED: Custom Rank Conditions"
            )

            continue

        # --------------------------------------------------
        # QUALIFIED
        # --------------------------------------------------

        print("")
        print("================================")
        print(
            "QUALIFIED:",
            rank.rank_name
        )
        print("================================")

        return rank

    # ------------------------------------------------------
    # NO RANK
    # ------------------------------------------------------

    print("")
    print("--------------------------------")
    print(
        "No rank qualified for:",
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
   

    # ------------------------------------------------------
    # CHECK IF THIS RANK WAS ALREADY ASSIGNED
    # ------------------------------------------------------

    existing = (
        db.query(UserRankHistory)
        .filter(
            UserRankHistory.user_id == user.id,
            UserRankHistory.rank_id == rank.id
        )
        .first()
    )

    if existing:

        print(
            "Rank already assigned:",
            rank.rank_name
        )

        return None

    # ------------------------------------------------------
    # UPDATE CURRENT RANK
    # ------------------------------------------------------

    user.current_rank_id = rank.id

    # ------------------------------------------------------
    # RANK REWARD
    # ------------------------------------------------------

    reward_amount = float(
        rank.reward_income or 0
    )

    # ------------------------------------------------------
    # CREATE RANK HISTORY
    # ------------------------------------------------------

    history = UserRankHistory(

        user_id=user.id,

        rank_id=rank.id,

        reward_income=reward_amount,

        reward_paid=False,

        paid_at=None

    )

    db.add(history)

    db.flush()

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
        "Status:",
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
    

    # ------------------------------------------------------
    # CHECK ALREADY PAID
    # ------------------------------------------------------

    if history.reward_paid:

        print(
            "Rank reward already paid:",
            history.id
        )

        return history

    # ------------------------------------------------------
    # REWARD AMOUNT
    # ------------------------------------------------------

    reward_amount = float(
        history.reward_income or 0
    )

    if reward_amount <= 0:

        print(
            "Rank reward is zero:",
            history.id
        )

        return history

    # ------------------------------------------------------
    # GET WALLET
    # ------------------------------------------------------

    wallet = (
        db.query(Wallet)
        .filter(
            Wallet.user_id == history.user_id
        )
        .first()
    )

    # ------------------------------------------------------
    # CREATE WALLET IF MISSING
    # ------------------------------------------------------

    if not wallet:

        wallet = Wallet(
            user_id=history.user_id,
            balance=0,
            pending_balance=0,
            admin_fee=0
        )

        db.add(wallet)

        db.flush()

    # ------------------------------------------------------
    # CURRENT WALLET VALUES
    # ------------------------------------------------------

    wallet_balance_before = float(
        wallet.balance or 0
    )

    pending_before = float(
        wallet.pending_balance or 0
    )

    # ------------------------------------------------------
    # ADD TO PENDING BALANCE
    # ------------------------------------------------------

    wallet.pending_balance = (
        pending_before
        + reward_amount
    )

    # ------------------------------------------------------
    # CREATE WALLET TRANSACTION
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # KEEP RANK HISTORY PENDING
    # ------------------------------------------------------

    history.reward_paid = False

    history.paid_at = None

    db.flush()

    # ------------------------------------------------------
    # LOGS
    # ------------------------------------------------------

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
    

    print("")
    print("==========================================")
    print("CHECK AND ASSIGN RANK")
    print("User:", user.user_id)
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

        if not active_investment:

            print(
                "NO ACTIVE INVESTMENT"
            )

            print(
                "Rank reward skipped for:",
                user.user_id
            )

            return None

        print(
            "Active investment found:",
            active_investment.id
        )

        # ==================================================
        # 2. FIND HIGHEST QUALIFIED RANK
        # ==================================================

        rank = get_highest_qualified_rank(
            db,
            user
        )

        if not rank:

            print(
                "No qualified rank."
            )

            return None

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

        if not history:

            print(
                "Rank was not assigned."
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
        # 6. REFRESH
        # ==================================================

        db.refresh(history)

        print("")
        print("==========================================")
        print("RANK PROCESS COMPLETED SUCCESSFULLY")
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

        print(
            "Rank process failed:",
            str(e)
        )

        raise
