from mcts_node import MCTSNode
from p2_t3 import Board
from random import choice
from math import sqrt, log, e

num_nodes = 100
explore_faction = 2.


def calculates_score(node: MCTSNode, child: MCTSNode):
    wins = child.wins
    visits = child.visits
    total_visits = node.visits
    exploitation_factor = (wins / visits)
    exploration_factor = explore_faction * sqrt(log(total_visits, e) / visits)
    value = exploitation_factor + exploration_factor
    return value


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


def get_heuristic(board: Board, state, bot_identity):
    board_state = board.owned_boxes(state)
    player = bot_identity
    bot = 3 - bot_identity
    is_player_turn = board.current_player(state) == player
    player_score = 0
    bot_score = 0
    for r in range(3):
        row = [board_state[(r, 0)], board_state[(r, 1)], board_state[(r, 2)]]
        if all(row) is player:
            return 8 if is_player_turn else -8
        elif all(row) is bot:
            return -8 if is_player_turn else -8
        if player in row and bot in row:
            continue
        elif player in row:
            player_score += 1
        elif bot in row:
            bot_score += 1
        else:
            player_score += 1
            bot_score += 1

    for c in range(3):
        col = [board_state[(0, c)], board_state[(1, c)], board_state[(2, c)]]
        if all(col) is player:
            return 8 if is_player_turn else -8
        elif all(col) is bot:
            return -8 if is_player_turn else 8
        if player in col and bot in col:
            continue
        elif player in col:
            player_score += 1
        elif bot in col:
            bot_score += 1
        else:
            player_score += 1
            bot_score += 1

    diag = [board_state[(0, 0)], board_state[(1, 1)], board_state[(2, 2)]]
    if all(diag) is player:
        return 8 if is_player_turn else -8
    elif all(diag) is bot:
        return -8 if is_player_turn else 8
    if player in diag and bot in diag:
        pass
    elif player in diag:
        player_score += 1
    elif bot in diag:
        bot_score += 1
    else:
        player_score += 1
        bot_score += 1

    diag = [board_state[(0, 2)], board_state[(1, 1)], board_state[(2, 0)]]
    if all(diag) is player:
        return 8 if is_player_turn else -8
    elif all(diag) is bot:
        return -8 if is_player_turn else 8
    if player in diag and bot in diag:
        pass
    elif player in diag:
        player_score += 1
    elif bot in diag:
        bot_score += 1
    else:
        player_score += 1
        bot_score += 1
    return (player_score - bot_score) if is_player_turn else (bot_score - player_score)


def rollout(board: Board, state, bot_identity: int):
    """ Given the state of the game, the rollout plays out the remainder randomly.

    Args:
        board:  The game setup.
        state:  The state of the game.
        bot_identity: Player number

    Returns:
        state: The terminal game state

    """
    # for action in actions:
    # new_state = board.next_state(state, action)
    # if board.is_ended(new_state) and is_win(board, new_state, bot_identity):
    #     return new_state

    # get a random legal action
    # get new state from action
    # repeat until game ends
    # h(x)
    # rows x can win - rows o can win
    # if x wins a row, +inf
    # if lose, -inf
    # print("STATE:", state)
    # print("UNPACK STATE:", board.unpack_state(state))

    #two checks
    # check small board for is_winning, is_losing, stalemate/draw
    # keep track in our own board rep
    # calc heuristic on big board, reverse heuristic on opponent's turn

    while not board.is_ended(state):
        actions = board.legal_actions(state)
        best_score = float('-inf')
        best_action = None
        for action in actions:
            next_state = board.next_state(state, action)
            if board.is_ended(next_state) and is_win(board, next_state, bot_identity):
                return next_state
            score = get_heuristic(board, state, bot_identity)
            if score >= best_score:
                best_action = action
                best_score = score
        state = board.next_state(state, best_action)
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
    temp_state = board.next_state(state, best_action)
    h = get_heuristic(board, temp_state, bot_identity)
    print("Heuristic: ", h)

    print(f"Action chosen: {best_action}")
    return best_action
