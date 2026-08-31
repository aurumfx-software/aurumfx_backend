# # from sqlalchemy.orm import Session
# # from sqlalchemy import func

# # from app.models import User, Investment


# # def build_user_genealogy_tree(
# #     db: Session,
# #     user: User
# # ):
# #     # -----------------------------------------
# #     # Total approved investment
# #     # -----------------------------------------
# #     total_investment = (
# #         db.query(
# #             func.coalesce(
# #                 func.sum(Investment.amount),
# #                 0
# #             )
# #         )
# #         .filter(
# #             Investment.user_id == user.id,
# #             Investment.approval_status == "APPROVED"
# #         )
# #         .scalar()
# #     )

# #     # -----------------------------------------
# #     # Total approved lots
# #     # -----------------------------------------
# #     total_lots = (
# #         db.query(
# #             func.coalesce(
# #                 func.sum(Investment.lots),
# #                 0
# #             )
# #         )
# #         .filter(
# #             Investment.user_id == user.id,
# #             Investment.approval_status == "APPROVED"
# #         )
# #         .scalar()
# #     )

# #     # -----------------------------------------
# #     # Direct members
# #     # -----------------------------------------
# #     children = (
# #         db.query(User)
# #         .filter(
# #             User.enroller_id == user.user_id
# #         )
# #         .all()
# #     )

# #     return {
# #         "user_id": user.user_id,

# #         "full_name": (
# #             f"{user.first_name} {user.last_name}"
# #         ).strip(),

# #         "date_of_join": user.created_at,

# #         "rank": (
# #             user.current_rank.rank_name
# #             if user.current_rank
# #             else None
# #         ),

# #         "total_investment": float(
# #             total_investment or 0
# #         ),

# #         "total_lots": int(
# #             total_lots or 0
# #         ),

# #         "children": [
# #             build_user_genealogy_tree(
# #                 db,
# #                 child
# #             )
# #             for child in children
# #         ]
# #     }


# # def get_logged_in_user_genealogy(
# #     db: Session,
# #     user_id: str
# # ):
# #     # get_current_user returns user_id string
# #     user = (
# #         db.query(User)
# #         .filter(
# #             User.user_id == user_id
# #         )
# #         .first()
# #     )

# #     if not user:
# #         return None

# #     return build_user_genealogy_tree(
# #         db,
# #         user
# #     )

# # def get_user_genealogy_list(
# #     db: Session,
# #     user_id: str
# # ):
# #     """
# #     Return logged-in user's genealogy as a flat list.

# #     Level 1 = direct enrollers
# #     Level 2 = their direct enrollers
# #     Level 3 = next level
# #     """

# #     root_user = (
# #         db.query(User)
# #         .filter(
# #             User.user_id == user_id
# #         )
# #         .first()
# #     )

# #     if not root_user:
# #         return None

# #     result = []

# #     def collect_members(
# #         current_user: User,
# #         current_level: int
# #     ):
# #         children = (
# #             db.query(User)
# #             .filter(
# #                 User.enroller_id == current_user.user_id
# #             )
# #             .all()
# #         )

# #         for child in children:

# #             # Total investment
# #             total_investment = (
# #                 db.query(
# #                     func.coalesce(
# #                         func.sum(Investment.amount),
# #                         0
# #                     )
# #                 )
# #                 .filter(
# #                     Investment.user_id == child.id,
# #                     Investment.approval_status == "APPROVED"
# #                 )
# #                 .scalar()
# #             )

# #             # Total lots
# #             total_lots = (
# #                 db.query(
# #                     func.coalesce(
# #                         func.sum(Investment.lots),
# #                         0
# #                     )
# #                 )
# #                 .filter(
# #                     Investment.user_id == child.id,
# #                     Investment.approval_status == "APPROVED"
# #                 )
# #                 .scalar()
# #             )

# #             result.append({
# #                 "user_id": child.user_id,

# #                 "full_name": (
# #                     f"{child.first_name} {child.last_name}"
# #                 ).strip(),

# #                 "date_of_join": child.created_at,

# #                 "level": current_level,

# #                 "rank": (
# #                     child.current_rank.rank_name
# #                     if child.current_rank
# #                     else None
# #                 ),

# #                 "total_investment": float(
# #                     total_investment or 0
# #                 ),

# #                 "total_lots": int(
# #                     total_lots or 0
# #                 )
# #             })

# #             # Continue to next level
# #             collect_members(
# #                 child,
# #                 current_level + 1
# #             )

# #     collect_members(
# #         root_user,
# #         1
# #     )

# #     return result

# from sqlalchemy.orm import Session
# from sqlalchemy import func

# from app.models import User, Investment


# # ============================================================
# # BUILD ONE GENEALOGY NODE
# # ============================================================

# def build_genealogy_node(
#     db: Session,
#     user: User
# ):
#     # --------------------------------------------------------
#     # Profile image
#     # --------------------------------------------------------

#     profile_image = getattr(
#         user,
#         "profile_image",
#         None
#     )

#     # --------------------------------------------------------
#     # Full name
#     # --------------------------------------------------------

#     fullname = (
#         f"{user.first_name or ''} "
#         f"{user.last_name or ''}"
#     ).strip()

#     # --------------------------------------------------------
#     # Date of joining
#     # --------------------------------------------------------

#     date_of_joining = (
#         user.created_at.date()
#         if user.created_at
#         else None
#     )

#     # --------------------------------------------------------
#     # Rank
#     # --------------------------------------------------------

#     rank = None

#     if user.current_rank:
#         rank = user.current_rank.rank_name

#     # --------------------------------------------------------
#     # Investment information
#     # --------------------------------------------------------

#     investment_data = (
#         db.query(
#             func.coalesce(
#                 func.sum(Investment.amount),
#                 0
#             ),
#             func.coalesce(
#                 func.sum(Investment.lots),
#                 0
#             )
#         )
#         .filter(
#             Investment.user_id == user.id,
#             Investment.approval_status == "APPROVED",
#             Investment.investment_status == "ACTIVE"
#         )
#         .first()
#     )

#     total_investment = float(
#         investment_data[0] or 0
#     )

#     total_lots = int(
#         investment_data[1] or 0
#     )

#     # --------------------------------------------------------
#     # Investment status
#     # --------------------------------------------------------

#     active_investment = (
#         db.query(Investment.id)
#         .filter(
#             Investment.user_id == user.id,
#             Investment.approval_status == "APPROVED",
#             Investment.investment_status == "ACTIVE"
#         )
#         .first()
#     )

#     investment_status = (
#         "ACTIVE"
#         if active_investment
#         else "INACTIVE"
#     )

#     # --------------------------------------------------------
#     # Children
#     # --------------------------------------------------------

#     children = (
#         db.query(User)
#         .filter(
#             User.enroller_id == user.user_id,
#             User.role == "USER"
#         )
#         .order_by(
#             User.created_at.asc()
#         )
#         .all()
#     )

#     child_nodes = []

#     for child in children:
#         child_nodes.append(
#             build_genealogy_node(
#                 db,
#                 child
#             )
#         )

#     # --------------------------------------------------------
#     # Return node
#     # --------------------------------------------------------

#     return {
#         "user_id": user.user_id,
#         "profile_image": profile_image,
#         "fullname": fullname,
#         "date_of_joining": date_of_joining,
#         "rank": rank,
#         "total_investment": total_investment,
#         "total_lots": total_lots,
#         "investment_status": investment_status,
#         "children": child_nodes
#     }


# # ============================================================
# # GET GENEALOGY BY USER ID
# # ============================================================

# def get_user_genealogy(
#     db: Session,
#     user_id: str
# ):
#     """
#     Find user using user_id such as FX002
#     and return that user's complete subtree.
#     """

#     user = (
#         db.query(User)
#         .filter(
#             User.user_id == user_id
#         )
#         .first()
#     )

#     if not user:
#         return None

#     return build_genealogy_node(
#         db,
#         user
#     )


# # ============================================================
# # GET LOGGED-IN USER GENEALOGY
# # ============================================================

# def get_logged_in_user_genealogy(
#     db: Session,
#     current_user: str
# ):
#     return get_user_genealogy(
#         db,
#         current_user
#     )


# # ============================================================
# # GET FLAT GENEALOGY
# # ============================================================

# def get_user_genealogy_list(
#     db: Session,
#     user_id: str
# ):
#     user = (
#         db.query(User)
#         .filter(
#             User.user_id == user_id
#         )
#         .first()
#     )

#     if not user:
#         return None

#     result = []

#     def traverse(
#         parent_user: User,
#         level: int
#     ):
#         children = (
#             db.query(User)
#             .filter(
#                 User.enroller_id == parent_user.user_id,
#                 User.role == "USER"
#             )
#             .order_by(
#                 User.created_at.asc()
#             )
#             .all()
#         )

#         for child in children:

#             node = build_genealogy_node(
#                 db,
#                 child
#             )

#             node.pop(
#                 "children",
#                 None
#             )

#             node["level"] = level

#             result.append(node)

#             traverse(
#                 child,
#                 level + 1
#             )

#     traverse(
#         user,
#         1
#     )

#     return result


# # ============================================================
# # ADMIN - COMPLETE GENEALOGY
# # ============================================================

# def get_full_genealogy(
#     db: Session
# ):
#     """
#     Start from first ADMIN/root.
#     """

#     admin = (
#         db.query(User)
#         .filter(
#             User.role == "ADMIN"
#         )
#         .order_by(
#             User.id.asc()
#         )
#         .first()
#     )

#     if not admin:
#         return None

#     return build_genealogy_node(
#         db,
#         admin
#     )

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import User, Investment


# ============================================================
# GET USER INVESTMENT SUMMARY
# ============================================================

def get_user_investment_summary(
    db: Session,
    user: User
):
    """
    Get user's own ACTIVE + APPROVED investment details.
    """

    investment_data = (
        db.query(
            func.coalesce(
                func.sum(Investment.amount),
                0
            ),
            func.coalesce(
                func.sum(Investment.lots),
                0
            )
        )
        .filter(
            Investment.user_id == user.id,
            Investment.approval_status == "APPROVED",
            Investment.investment_status == "ACTIVE"
        )
        .first()
    )

    total_investment = float(
        investment_data[0] or 0
    )

    total_lots = int(
        investment_data[1] or 0
    )

    return total_investment, total_lots


# ============================================================
# BUILD ONE GENEALOGY NODE
# ============================================================

def build_genealogy_node(
    db: Session,
    user: User
):
    # --------------------------------------------------------
    # Profile image
    # --------------------------------------------------------

    profile_image = getattr(
        user,
        "profile_image",
        None
    )

    # --------------------------------------------------------
    # Full name
    # --------------------------------------------------------

    fullname = (
        f"{user.first_name or ''} "
        f"{user.last_name or ''}"
    ).strip()

    # --------------------------------------------------------
    # Date of joining
    # --------------------------------------------------------

    date_of_joining = (
        user.created_at.date()
        if user.created_at
        else None
    )

    # --------------------------------------------------------
    # Rank
    # --------------------------------------------------------

    rank = None

    if user.current_rank:
        rank = user.current_rank.rank_name

    # --------------------------------------------------------
    # OWN INVESTMENT
    # --------------------------------------------------------

    (
        total_investment,
        total_lots
    ) = get_user_investment_summary(
        db,
        user
    )

    # --------------------------------------------------------
    # Investment status
    # --------------------------------------------------------

    active_investment = (
        db.query(Investment.id)
        .filter(
            Investment.user_id == user.id,
            Investment.approval_status == "APPROVED",
            Investment.investment_status == "ACTIVE"
        )
        .first()
    )

    investment_status = (
        "ACTIVE"
        if active_investment
        else "INACTIVE"
    )

    # --------------------------------------------------------
    # Children
    # --------------------------------------------------------

    children = (
        db.query(User)
        .filter(
            User.enroller_id == user.user_id,
            User.role == "USER"
        )
        .order_by(
            User.created_at.asc()
        )
        .all()
    )

    child_nodes = []

    # --------------------------------------------------------
    # GROUP LOTS
    #
    # Start with user's own lots.
    # Then add every child's group lots.
    # --------------------------------------------------------

    total_group_lots = total_lots

    for child in children:

        child_node = build_genealogy_node(
            db,
            child
        )

        child_nodes.append(
            child_node
        )

        total_group_lots += (
            child_node["total_group_lots"]
        )

    # --------------------------------------------------------
    # Return node
    # --------------------------------------------------------

    return {
        "user_id": user.user_id,

        "profile_image": profile_image,

        "fullname": fullname,

        "date_of_joining": date_of_joining,

        "rank": rank,

        # User's own active approved investment
        "total_investment": total_investment,

        # User's own active approved lots
        "total_lots": total_lots,

        # User + complete downline lots
        "total_group_lots": total_group_lots,

        "investment_status": investment_status,

        "children": child_nodes
    }


# ============================================================
# GET GENEALOGY BY USER ID
# ============================================================

def get_user_genealogy(
    db: Session,
    user_id: str
):
    """
    Find user using user_id such as FX002
    and return that user's complete subtree.
    """

    user = (
        db.query(User)
        .filter(
            User.user_id == user_id
        )
        .first()
    )

    if not user:
        return None

    return build_genealogy_node(
        db,
        user
    )


# ============================================================
# GET LOGGED-IN USER GENEALOGY
# ============================================================

def get_logged_in_user_genealogy(
    db: Session,
    current_user: str
):
    return get_user_genealogy(
        db,
        current_user
    )


# ============================================================
# GET FLAT GENEALOGY
# ============================================================

def get_user_genealogy_list(
    db: Session,
    user_id: str
):
    user = (
        db.query(User)
        .filter(
            User.user_id == user_id
        )
        .first()
    )

    if not user:
        return None

    result = []

    def traverse(
        parent_user: User,
        level: int
    ):
        children = (
            db.query(User)
            .filter(
                User.enroller_id == parent_user.user_id,
                User.role == "USER"
            )
            .order_by(
                User.created_at.asc()
            )
            .all()
        )

        for child in children:

            node = build_genealogy_node(
                db,
                child
            )

            # Save children before removing it
            # because traverse() needs the database
            # hierarchy separately.
            node.pop(
                "children",
                None
            )

            node["level"] = level

            result.append(node)

            traverse(
                child,
                level + 1
            )

    traverse(
        user,
        1
    )

    return result


# ============================================================
# ADMIN - COMPLETE GENEALOGY
# ============================================================

def get_full_genealogy(
    db: Session
):
    """
    Start from the first ADMIN/root.
    """

    admin = (
        db.query(User)
        .filter(
            User.role == "ADMIN"
        )
        .order_by(
            User.id.asc()
        )
        .first()
    )

    if not admin:
        return None

    return build_genealogy_node(
        db,
        admin
    )