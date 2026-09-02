# from sqlalchemy.orm import Session
# from sqlalchemy import func
# from datetime import datetime

# from app.models import (
#     User,
#     Investment,
#     RankCondition,
#     RankSetting,
#     UserRankHistory,
#     Wallet,
#     WalletTransaction
# )
# def get_self_lots(db: Session, user_id: int):

#     return (
#         db.query(
#             func.coalesce(func.sum(Investment.lots), 0)
#         )
#         .filter(
#             Investment.user_id == user_id,
#             Investment.approval_status == "APPROVED"
#         )
#         .scalar()
#     )
# def get_team_lots(db: Session, user: User):

#     total = get_self_lots(db, user.id)

#     children = (
#         db.query(User)
#         .filter(
#             User.enroller_id == user.user_id
#         )
#         .all()
#     )

#     for child in children:
#         total += get_team_lots(db, child)

#     return total

# def get_direct_sponsor_group_lots(
#     db: Session,
#     user: User
# ):

#     directs = (
#         db.query(User)
#         .filter(
#             User.enroller_id == user.user_id
#         )
#         .all()
#     )

#     group_lots = []

#     for sponsor in directs:

#         lots = get_team_lots(
#             db,
#             sponsor
#         )

#         group_lots.append(lots)

#     group_lots.sort(reverse=True)

#     return group_lots

# def check_rank_conditions(
#     db: Session,
#     rank,
#     group_lots: list[int]
# ):
#     """
#     Check whether a user satisfies all conditions for a rank.

#     Example:
#     group_lots = [5200,1200,900,70,55]
#     """

#     remaining_groups = group_lots.copy()

#     conditions = (
#         db.query(RankCondition)
#         .filter(
#             RankCondition.rank_id == rank.id
#         )
#         .order_by(
#             RankCondition.order_no
#         )
#         .all()
#     )

#     for condition in conditions:

#         matched = []

#         for lots in remaining_groups:

#             if lots >= condition.minimum_group_lots:
#                 matched.append(lots)

#         if len(matched) < condition.required_group_count:
#             return False

#         matched.sort(reverse=True)

#         matched = matched[:condition.required_group_count]

#         for value in matched:
#             remaining_groups.remove(value)

#     return True

# def get_highest_qualified_rank(
#     db: Session,
#     user: User
# ):
#     print("--------------------------------")
#     print("Checking :", user.user_id)

#     total_lots = get_team_lots(db, user)

#     group_lots = get_direct_sponsor_group_lots(db, user)

#     print("Total Lots :", total_lots)
#     print("Group Lots :", group_lots)

#     ranks = (
#         db.query(RankSetting)
#         .filter(
#             RankSetting.status == True
#         )
#         .order_by(
#             RankSetting.rank_no.desc()
#         )
#         .all()
#     )

#     for rank in ranks:

#         if total_lots < rank.minimum_total_lots:
#             continue

#         if len(group_lots) < rank.minimum_direct_sponsors:
#             continue

#         if check_rank_conditions(
#             db,
#             rank,
#             group_lots
#         ):
#             return rank

#     return None

# def assign_rank(
#     db: Session,
#     user: User,
#     rank: RankSetting
# ):

#     existing = (
#         db.query(UserRankHistory)
#         .filter(
#             UserRankHistory.user_id == user.id,
#             UserRankHistory.rank_id == rank.id
#         )
#         .first()
#     )

#     if existing:
#         return None

#     user.current_rank_id = rank.id

#     history = UserRankHistory(
#         user_id=user.id,
#         rank_id=rank.id,
#         reward_income=rank.reward_income,
#         reward_paid=False
#     )

#     db.add(history)

#     db.commit()

#     db.refresh(history)

#     return history


# def credit_rank_reward(
#     db: Session,
#     history: UserRankHistory
# ):

#     if history.reward_paid:
#         return

#     wallet = (
#         db.query(Wallet)
#         .filter(
#             Wallet.user_id == history.user_id
#         )
#         .first()
#     )

#     if not wallet:

#         wallet = Wallet(
#             user_id=history.user_id,
#             balance=0
#         )

#         db.add(wallet)

#         db.commit()

#         db.refresh(wallet)

#     wallet.balance += history.reward_income

#     transaction = WalletTransaction(

#         wallet_id=wallet.id,

#         investment_id=None,

#         amount=history.reward_income,

#         transaction_type="RANK_REWARD",

#         remarks=f"Reward for Rank ID {history.rank_id}"

#     )

#     db.add(transaction)

#     history.reward_paid = True

#     history.paid_at = datetime.utcnow()

#     db.commit()

# def check_and_assign_rank(
#     db: Session,
#     user: User
# ):
#     print("========== CHECK RANK ==========")
#     print("User :", user.user_id)
#     rank = get_highest_qualified_rank(
#         db,
#         user
#     )

#     if not rank:
#         return

#     history = assign_rank(
#         db,
#         user,
#         rank
#     )

#     if not history:
#         return

#     credit_rank_reward(
#         db,
#         history
#     )

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
    Get total approved investment lots
    directly owned by the user.
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
    Get user's own approved lots
    + all approved downline team lots.
    """

    total = get_self_lots(
        db,
        user.id
    )

    children = (
        db.query(User)
        .filter(
            User.enroller_id == user.user_id
        )
        .all()
    )

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
    Get total team lots for each direct sponsor group.

    Example:

        User
        ├── A -> 500 lots
        ├── B -> 300 lots
        └── C -> 100 lots

    Result:

        [500, 300, 100]
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

        lots = get_team_lots(
            db,
            sponsor
        )

        group_lots.append(
            int(lots)
        )

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
    """
    Check all custom group conditions for a rank.

    The same sponsor group cannot be reused
    for multiple conditions.
    """

    remaining_groups = group_lots.copy()

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
    # No custom conditions
    # ------------------------------------------------------

    if not conditions:
        return True

    # ------------------------------------------------------
    # Check each condition
    # ------------------------------------------------------

    for condition in conditions:

        matched = []

        for lots in remaining_groups:

            if (
                lots
                >= condition.minimum_group_lots
            ):
                matched.append(lots)

        # --------------------------------------------------
        # Not enough groups
        # --------------------------------------------------

        if (
            len(matched)
            < condition.required_group_count
        ):
            return False

        # --------------------------------------------------
        # Highest groups first
        # --------------------------------------------------

        matched.sort(
            reverse=True
        )

        selected = matched[
            :condition.required_group_count
        ]

        # --------------------------------------------------
        # Remove selected groups
        # --------------------------------------------------

        for value in selected:

            remaining_groups.remove(
                value
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
    """

    print("--------------------------------")
    print(
        "Checking Rank For:",
        user.user_id
    )

    # ------------------------------------------------------
    # Total team lots
    # ------------------------------------------------------

    total_lots = get_team_lots(
        db,
        user
    )

    # ------------------------------------------------------
    # Direct sponsor group lots
    # ------------------------------------------------------

    group_lots = (
        get_direct_sponsor_group_lots(
            db,
            user
        )
    )

    print(
        "Total Lots:",
        total_lots
    )

    print(
        "Group Lots:",
        group_lots
    )

    # ------------------------------------------------------
    # Get highest ranks first
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
    # Check each rank
    # ------------------------------------------------------

    for rank in ranks:

        print(
            "Checking Rank:",
            rank.rank_name,
            "| Rank No:",
            rank.rank_no
        )

        # --------------------------------------------------
        # Minimum total lots
        # --------------------------------------------------

        if (
            total_lots
            < rank.minimum_total_lots
        ):

            print(
                "Failed minimum total lots"
            )

            continue

        # --------------------------------------------------
        # Minimum direct sponsors
        # --------------------------------------------------

        if (
            len(group_lots)
            < rank.minimum_direct_sponsors
        ):

            print(
                "Failed minimum direct sponsors"
            )

            continue

        # --------------------------------------------------
        # Custom conditions
        # --------------------------------------------------

        if check_rank_conditions(
            db,
            rank,
            group_lots
        ):

            print(
                "QUALIFIED:",
                rank.rank_name
            )

            return rank

        print(
            "Failed rank conditions"
        )

    # ------------------------------------------------------
    # No rank qualified
    # ------------------------------------------------------

    print(
        "No rank qualified for:",
        user.user_id
    )

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
    Assign a newly qualified rank.

    Creates UserRankHistory with:

        reward_paid = False

    This means the reward is PENDING.

    No commit is performed here.
    """

    # ------------------------------------------------------
    # Prevent duplicate rank history
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
    # Update current rank
    # ------------------------------------------------------

    user.current_rank_id = rank.id

    # ------------------------------------------------------
    # Rank reward
    # ------------------------------------------------------

    reward_amount = float(
        rank.reward_income or 0
    )

    # ------------------------------------------------------
    # Create rank history
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
    """
    Add rank reward to wallet.pending_balance.

    IMPORTANT:

    Do NOT add the reward to wallet.balance.

    wallet.balance
        = already paid/available income

    wallet.pending_balance
        = generated but not yet paid income

    Admin fee is NOT deducted here.

    Admin fee is calculated only during payout
    from total:

        Referral
        + Level
        + Rank
    """

    # ------------------------------------------------------
    # Already paid
    # ------------------------------------------------------

    if history.reward_paid:

        print(
            "Rank reward already paid:",
            history.id
        )

        return history

    # ------------------------------------------------------
    # Reward amount
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
    # Get wallet
    # ------------------------------------------------------

    wallet = (
        db.query(Wallet)
        .filter(
            Wallet.user_id == history.user_id
        )
        .first()
    )

    # ------------------------------------------------------
    # Create wallet if missing
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
    #
    # IMPORTANT:
    #
    # DO NOT DO:
    #
    # wallet.balance += reward_amount
    #
    # Instead:
    # ------------------------------------------------------

    wallet.pending_balance = (
        pending_before
        + reward_amount
    )

    # ------------------------------------------------------
    # Create wallet transaction
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
    # Keep rank history PENDING
    # ------------------------------------------------------

    history.reward_paid = False

    history.paid_at = None

    db.flush()

    # ------------------------------------------------------
    # Logs
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


# # ==========================================================
# # CHECK AND ASSIGN RANK
# # ==========================================================

# def check_and_assign_rank(
#     db: Session,
#     user: User
# ):
#     """
#     Complete rank qualification flow.

#     Flow:

#         1. Check highest qualified rank
#         2. Create rank history
#         3. Set reward_paid=False
#         4. Add reward to pending_balance
#         5. Create PENDING wallet transaction
#         6. Commit everything together

#     Admin fee is NOT calculated here.
#     """

#     print(
#         "=========================================="
#     )

#     print(
#         "CHECK AND ASSIGN RANK"
#     )

#     print(
#         "User:",
#         user.user_id
#     )

#     print(
#         "=========================================="
#     )

#     try:

#         # --------------------------------------------------
#         # Find highest qualified rank
#         # --------------------------------------------------

#         rank = get_highest_qualified_rank(
#             db,
#             user
#         )

#         if not rank:

#             print(
#                 "No qualified rank."
#             )

#             return None

#         # --------------------------------------------------
#         # Assign rank
#         # --------------------------------------------------

#         history = assign_rank(
#             db,
#             user,
#             rank
#         )

#         if not history:

#             return None

#         # --------------------------------------------------
#         # Add reward to pending wallet
#         # --------------------------------------------------

#         credit_rank_reward(
#             db,
#             history
#         )

#         # --------------------------------------------------
#         # Commit entire transaction
#         # --------------------------------------------------

#         db.commit()

#         # --------------------------------------------------
#         # Refresh history
#         # --------------------------------------------------

#         db.refresh(history)

#         print(
#             "Rank process completed successfully."
#         )

#         print(
#             "Rank:",
#             rank.rank_name
#         )

#         print(
#             "Reward:",
#             history.reward_income
#         )

#         print(
#             "Reward Status:",
#             "PENDING"
#         )

#         return history

#     except Exception as e:

#         db.rollback()

#         print(
#             "Rank process failed:",
#             str(e)
#         )

#         raise

# ==========================================================
# CHECK AND ASSIGN RANK
# ==========================================================

def check_and_assign_rank(
    db: Session,
    user: User
):
    """
    Rank qualification flow.

    Rules:
        1. Check whether user has ACTIVE + APPROVED investment.
        2. Check Rank Settings / Rank Conditions.
        3. If qualified, assign rank.
        4. Only then create rank reward.
    """

    print("==========================================")
    print("CHECK AND ASSIGN RANK")
    print("User:", user.user_id)
    print("==========================================")

    try:

        # ==================================================
        # 1. CHECK ACTIVE INVESTMENT
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

        db.refresh(history)

        print(
            "Rank process completed successfully."
        )

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
            "Reward Status: PENDING"
        )

        return history

    except Exception as e:

        db.rollback()

        print(
            "Rank process failed:",
            str(e)
        )

        raise