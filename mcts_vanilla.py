from mcts_node import MCTSNode
from p2_t3 import Board
from random import choice
from math import sqrt, log, e

num_nodes = 100
explore_faction = 2.


def calculates_score(node: MCTSNode, child: MCTSNode):
    wins = child.wins
    vists = child.visits
    total_vists = node.visits
    explotation_factor = (wins / vists)
    exploration_factor = explore_faction * sqrt(log(total_vists, e) / vists)
    value = explotation_factor + exploration_factor
    return value


def traverse_nodes(node: MCTSNode, board: Board, state, bot_identity: int):
    """ Traverses the tree until the end criterion are met.
    e.g. find the best expandable node (node with untried action) if it exist,
    or else a terminal node

    Args:
        node:       A tree node from which the search is traversing.
        board:      The game setup.
        state:      The state of the game.
        identity:   The bot's identity, either 1 or 2

    Returns:
        node: A node from which the next stage of the search can proceed.
        state: The state associated with that node

    """
    # best_score = 0
    # best_node = node if node.untried_actions else None
    # queue = []
    # terminal_node = [] # keeps track of visited terminal nodes
    # queue.append(node)
    # while(queue):
    #     n = queue.pop(0)
    #     n.visits += 1
    #     if(len(n.untried_actions) == 0):
    #         if is_win(board=board, state=state, identity_of_bot=bot_identity):
    #             return n, state
    #         terminal_node.append(n)
    #     for child in node.child_nodes:
    #         # cal score
    #         score = ucb(node, BOT IDENTITY)
    #         if score > best_score:
    #             best_node = child
    #             best_score = score
    # if best_node:
    #     return best_node, state # figure out state

    # if terminal_node:
    #     return terminal_node[0], state

    # from lecture slides: Walk the game tree picking child nodes with the highest value of this formula. Return a node with untried actions to expand.
    # stopping criteria: no node has untried actions OR game has ended
    is_current_player = False
    while (node is not None):  # is_win(board, state, bot_identity) == False
        # for each node, find the child with the highest value, and traverse that child using UCT algorithm
        if not node.child_nodes:
            break
        if len(node.untried_actions) == 0:
            # print("here")
            return node, state
        best_score = 0
        best_node = node
        best_action = None
        children = node.child_nodes
        for action, child in children.items():
            score = ucb(child, is_current_player)
            # print("score: ", score)
            if score >= best_score:
                best_score = score
                best_node = child
                best_action = action
        node = best_node
        is_current_player = not is_current_player
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
        return child, new_state
    return None, state


def rollout(board: Board, state):
    """ Given the state of the game, the rollout plays out the remainder randomly.

    Args:
        board:  The game setup.
        state:  The state of the game.
    
    Returns:
        state: The terminal game state

    """
    # get a random legal action
    # get new state from action
    # repeat until game ends
    while board.is_ended(state) == False:
        actions = board.legal_actions(state)
        action = choice(actions)
        state = board.next_state(state, action)

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
    """ Calcualtes the UCB value for the given node from the perspective of the bot

    Args:
        node:   A node.
        is_opponent: A boolean indicating whether or not the last action was performed by the MCTS bot
    Returns:
        The value of the UCB function for the given node
    """
    if not node.parent:
        return 0
    vists = node.visits
    if is_opponent == False:
        wins = node.wins
    else:
        wins = vists - node.wins
    total_vists = node.parent.visits
    explotation_factor = (wins / vists)
    exploration_factor = explore_faction * sqrt(log(total_vists, e) / vists)
    value = explotation_factor + exploration_factor
    return value


def get_best_action(root_node: MCTSNode):
    """ Selects the best action from the root node in the MCTS tree

    Args:
        root_node:   The root node
    Returns:
        action: The best action from the root node
    
    """
    action = None
    best_score = float('-inf')
    for taken_action, node in root_node.child_nodes.items():
        score = ucb(node, False)
        if score > best_score:
            best_score = score
            action = taken_action
    return action


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
        state = current_state
        node = root_node
        best_unexpanded_node, state = traverse_nodes(node, board, current_state, bot_identity)
        next_node, next_state = expand_leaf(best_unexpanded_node, board, state)
        terminal_state = rollout(board, next_state)
        win = is_win(board, terminal_state, bot_identity)
        backpropagate(next_node, win)

        # print("next node: ", best_unexpended_node, " state: ", state)

        # child_node, state = expand_leaf(best_unexpended_node, state)

        # Do MCTS - This is all you!
        # ...

    # Return an action, typically the most frequently used action (from the root) or the action with the best
    # estimated win rate.
    best_action = get_best_action(root_node)

    print(f"Action chosen: {best_action}")
    return best_action
