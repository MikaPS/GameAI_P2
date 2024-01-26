from mcts_node import MCTSNode
from p2_t3 import Board
from random import choice
from math import sqrt, log, e

num_nodes = 1000
explore_faction = 2.

positions = dict(
    ((r, c), 1 << (3 * r + c))
    for r in range(3)
    for c in range(3)
)


def traverse_nodes(node: MCTSNode, board: Board, state, bot_identity: int):
    """ Traverses the tree until the end criterion are met.
    e.g. find the best expandable node (node with untried action) if it exist,
    or else a terminal node

    Args:
        node:       A tree node from which the search is traversing.
        board:      The game setup.
        state:      The state of the game.
        bot_identity:   The bot's identity, either 1 or 2

    Returns:
        node: A node from which the next stage of the search can proceed.
        state: The state associated with that node

    """

    # from lecture slides: Walk the game tree picking child nodes with the highest value of this formula. Return a node with untried actions to expand.
    # stopping criteria: no node has untried actions OR game has ended
    if not node.child_nodes:
        return node, state
    is_opponent = board.current_player(state) != bot_identity
    while node is not None:
        # for each node,
        # find expandable node
        # else find the child with the UBC highest value,
        # and traverse that child

        # node with possible actions
        if node.untried_actions:
            return node, state

        # terminal node
        if not node.untried_actions and not node.child_nodes:
            return node, state

        best_node = node
        best_action = None
        best_score = float('-inf')
        children = node.child_nodes
        is_opponent = not is_opponent
        for action, child in children.items():
            score = ucb(child, is_opponent)
            if score > best_score:
                best_score = score
                best_node = child
                best_action = action
        node = best_node
        state = board.next_state(state, best_action)

    return node, state


def expand_leaf(node: MCTSNode, board: Board, state):
    """ Adds a new leaf to the tree by creating a new child node for the given node (if it is non-terminal).

    Args:
        node:   The node for which a child will be added.
        board:  The game setup.
        state:  The state of the game.

    Returns:
        node: The added child node
        state: The state associated with that node

    """
    # check that node is non-terminal
    if node.untried_actions:
        action = choice(node.untried_actions)
        new_state = board.next_state(state, action)
        child_actions = board.legal_actions(new_state)  # node.untried_actions.remove(action)
        child = MCTSNode(parent=node, parent_action=action, action_list=child_actions)
        node.child_nodes.update({action: child})
        node.untried_actions.remove(action)
        return child, new_state
    return None, state


def get_subbox_score(board: Board, state, action, bot_identity):
    winning_combinations = [
        [(0, 0), (0, 1), (0, 2)],  # Row 1
        [(1, 0), (1, 1), (1, 2)],  # Row 2
        [(2, 0), (2, 1), (2, 2)],  # Row 3
        [(0, 0), (1, 0), (2, 0)],  # Column 1
        [(0, 1), (1, 1), (2, 1)],  # Column 2
        [(0, 2), (1, 2), (2, 2)],  # Column 3
        [(0, 0), (1, 1), (2, 2)],  # Diagonal from top-left to bottom-right
        [(0, 2), (1, 1), (2, 0)]  # Diagonal from top-right to bottom-left
    ]
    unpack = board.unpack_state(state)
    board_row = action[0]
    board_col = action[1]
    b = {(0, 0): 0, (0, 1): 0, (0, 2): 0, (1, 0): 0, (1, 1): 0, (1, 2): 0, (2, 0): 0, (2, 1): 0, (2, 2): 0}
    for piece in unpack['pieces']:
        if piece['outer-row'] == board_row and piece['outer-column'] == board_col:
            row_index = piece['inner-row']
            col_index = piece['inner-column']
            b[(row_index, col_index)] = piece['player']

    player_score = bot_score = 0
    player = bot_identity
    bot = 3 - bot_identity
    is_player_turn = (3 - board.current_player(state)) == player
    for combination in winning_combinations:
        values = [b[position] for position in combination]
        if all(value == 0 for value in values):
            player_score += 1
            bot_score += 1
        elif all(value == player for value in values):
            player_score = 8
            bot_score = 0
            break
        elif all(value == bot for value in values):
            bot_score = 8
            player_score = 0
            break
        elif player in values and bot in values:
            continue
        if player in values:
            player_score += 1
        if bot in values:
            bot_score += 1

    debug_msg = f"{action}\n{b}\n player score: {player_score} | bot score: {bot_score} "
    return (player_score - bot_score) if is_player_turn else (bot_score - player_score), debug_msg


def rollout(board: Board, state, bot_identity: int):
    """ Given the state of the game, the rollout plays out the remainder randomly.

    Args:
        board:  The game setup.
        state:  The state of the game.
        bot_identity: Player number

    Returns:
        state: The terminal game state

    """

    is_player_turn = board.current_player(state) == bot_identity
    while not board.is_ended(state):
        actions = board.legal_actions(state)
        # state = board.next_state(state, choice(actions))
        if not is_player_turn:
            state = board.next_state(state, choice(actions))
            is_player_turn = not is_player_turn
            continue
        best_score = float('-inf')
        best_action = None
        for action in actions:
            next_state = board.next_state(state, action)
            if board.is_ended(next_state) and is_win(board, next_state, bot_identity):
                return next_state
            score, _ = get_subbox_score(board, next_state, action, bot_identity)
            # score, _ = get_heuristic(board, next_state, bot_identity)
            # print(f"action: {action} | score: {score}")
            # score = get_heuristic(board, next_state, bot_identity)
            if score > best_score:
                best_action = action
                best_score = score
        # print(f'chose {best_action}')
        state = board.next_state(state, best_action)
        is_player_turn = not is_player_turn
    return state


def backpropagate(node: MCTSNode | None, won: bool):
    """ Navigates the tree from a leaf node to the root, updating the win and visit count of each node along the path.

    Args:
        node:   A leaf node.
        won:    An indicator of whether the bot won or lost the game.

    """
    while node is not None:
        node.visits += 1
        if won:
            node.wins += 1
        node = node.parent


def ucb(node: MCTSNode, is_opponent: bool):
    """ Calculates the UCB value for the given node from the perspective of the bot

    Args:
        node:   A node.
        is_opponent: A boolean indicating whether or not the last action was performed by the MCTS bot
    Returns:
        The value of the UCB function for the given node
    """
    if not node.parent:
        return 0
    visits = node.visits
    wins = node.wins if not is_opponent else visits - node.wins
    total_visits = node.parent.visits
    exploitation_factor = (wins / visits)
    exploration_factor = explore_faction * sqrt(log(total_visits, e) / visits)
    value = exploitation_factor + exploration_factor
    return value


def get_best_action(root_node: MCTSNode):
    """ Selects the best action from the root node in the MCTS tree

    Args:
        root_node:   The root node
    Returns:
        action: The best action from the root node
    
    """
    best_action = None
    best_score = float('-inf')
    for action, node in root_node.child_nodes.items():
        score = node.wins / node.visits
        if score > best_score:
            best_score = score
            best_action = action
    return best_action


def is_win(board: Board, state, identity_of_bot: int):
    # checks if state is a win state for identity_of_bot
    outcome = board.points_values(state)
    assert outcome is not None, "is_win was called on a non-terminal state"
    return outcome[identity_of_bot] == 1


def think(board: Board, current_state):
    """ Performs MCTS by sampling games and calling the appropriate functions to construct the game tree.

    Args:
        board:  The game setup.
        current_state:  The current state of the game.

    Returns:    The action to be taken from the current state

    """
    bot_identity = board.current_player(current_state)  # 1 or 2
    root_node = MCTSNode(parent=None, parent_action=None, action_list=board.legal_actions(current_state))

    for _ in range(num_nodes):
        node = root_node
        best_unexpanded_node, state = traverse_nodes(node, board, current_state, bot_identity)
        next_node, next_state = expand_leaf(best_unexpanded_node, board, state)
        terminal_state = rollout(board, next_state, bot_identity)
        win = is_win(board, terminal_state, bot_identity)
        backpropagate(next_node, win)

        # print("next node: ", best_unexpended_node, " state: ", state)

        # child_node, state = expand_leaf(best_unexpended_node, state)

        # Do MCTS - This is all you!
        # ...

    # Return an action, typically the most frequently used action (from the root) or the action with the best
    # estimated win rate.
    best_action = get_best_action(root_node)
    return best_action
