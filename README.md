# GameAI_P2
Hersh Rudrawal <br> Mika Peer Shalem

# Modifications
In our modified bot, we focused on winning the sub-boxes. Our heuristics gave a score to each possible action, ensuring that our bot chooses the best action in each round. 
The score is based on all the possible ways to win on the current board. The highest possible score is 8: 3 wins for rows, 3 for columns, and 2 for the diagonals. 
Therefore, if the action is a winning move, we give our player a score of 8 and the opponent 0 (since the opponent cannot make any more moves that lead to their win). We give each player a point if there’s an empty row, column, or diagonal. This way, players are rewarded for winning or placing pieces in areas that could lead to a win.

However, we do not forward check our move.
As a consequence, our opponent could win a subbox on their turn or block our win in a subbox.
Also, we do not check to block opponents from winning