from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.models import (
    User,
    Investment,
    RankCondition,
    RankSetting,
    UserRankHistory,
    Wallet,
    WalletTransaction
)
def get_self_lots(db: Session, user_id: int):

    return (
        db.query(
            func.coalesce(func.sum(Investment.lots), 0)
        )
        .filter(
            Investment.user_id == user_id,
            Investment.approval_status == "APPROVED"
        )
        .scalar()
    )
def get_team_lots(db: Session, user: User):

    total = get_self_lots(db, user.id)

    children = (
        db.query(User)
        .filter(
            User.enroller_id == user.user_id
        )
        .all()
    )

    for child in children:
        total += get_team_lots(db, child)

    return total

def get_direct_sponsor_group_lots(
    db: Session,
    user: User
):

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

        group_lots.append(lots)

    group_lots.sort(reverse=True)

    return group_lots

def check_rank_conditions(
    db: Session,
    rank,
    group_lots: list[int]
):
    """
    Check whether a user satisfies all conditions for a rank.

    Example:
    group_lots = [5200,1200,900,70,55]
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

    for condition in conditions:

        matched = []

        for lots in remaining_groups:

            if lots >= condition.minimum_group_lots:
                matched.append(lots)

        if len(matched) < condition.required_group_count:
            return False

        matched.sort(reverse=True)

        matched = matched[:condition.required_group_count]

        for value in matched:
            remaining_groups.remove(value)

    return True

def get_highest_qualified_rank(
    db: Session,
    user: User
):
    print("--------------------------------")
    print("Checking :", user.user_id)

    total_lots = get_team_lots(db, user)

    group_lots = get_direct_sponsor_group_lots(db, user)

    print("Total Lots :", total_lots)
    print("Group Lots :", group_lots)

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

    for rank in ranks:

        if total_lots < rank.minimum_total_lots:
            continue

        if len(group_lots) < rank.minimum_direct_sponsors:
            continue

        if check_rank_conditions(
            db,
            rank,
            group_lots
        ):
            return rank

    return None

def assign_rank(
    db: Session,
    user: User,
    rank: RankSetting
):

    existing = (
        db.query(UserRankHistory)
        .filter(
            UserRankHistory.user_id == user.id,
            UserRankHistory.rank_id == rank.id
        )
        .first()
    )

    if existing:
        return None

    user.current_rank_id = rank.id

    history = UserRankHistory(
        user_id=user.id,
        rank_id=rank.id,
        reward_income=rank.reward_income,
        reward_paid=False
    )

    db.add(history)

    db.commit()

    db.refresh(history)

    return history


def credit_rank_reward(
    db: Session,
    history: UserRankHistory
):

    if history.reward_paid:
        return

    wallet = (
        db.query(Wallet)
        .filter(
            Wallet.user_id == history.user_id
        )
        .first()
    )

    if not wallet:

        wallet = Wallet(
            user_id=history.user_id,
            balance=0
        )

        db.add(wallet)

        db.commit()

        db.refresh(wallet)

    wallet.balance += history.reward_income

    transaction = WalletTransaction(

        wallet_id=wallet.id,

        investment_id=None,

        amount=history.reward_income,

        transaction_type="RANK_REWARD",

        remarks=f"Reward for Rank ID {history.rank_id}"

    )

    db.add(transaction)

    history.reward_paid = True

    history.paid_at = datetime.utcnow()

    db.commit()

def check_and_assign_rank(
    db: Session,
    user: User
):
    print("========== CHECK RANK ==========")
    print("User :", user.user_id)
    rank = get_highest_qualified_rank(
        db,
        user
    )

    if not rank:
        return

    history = assign_rank(
        db,
        user,
        rank
    )

    if not history:
        return

    credit_rank_reward(
        db,
        history
    )