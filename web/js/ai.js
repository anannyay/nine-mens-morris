import { PLAYER_WHITE, PLAYER_BLACK } from './constants.js';
import { Move } from './state.js';

export class AIDifficulty{ constructor(name, depth, useAlphaBeta, allowRandom=false){ this.name=name; this.depth=depth; this.useAlphaBeta=useAlphaBeta; this.allowRandom=allowRandom; } }
export const EASY = new AIDifficulty('Easy', 1, false, true);
export const MEDIUM = new AIDifficulty('Medium', 3, true, false);
export const HARD = new AIDifficulty('Hard', 5, true, false);

export function evaluate(state, maximizingPlayer){
  const opponent = -maximizingPlayer;
  const myPieces = state.numPieces(maximizingPlayer);
  const oppPieces = state.numPieces(opponent);
  if(state.winner === maximizingPlayer) return 10000.0;
  if(state.winner === opponent) return -10000.0;
  const currentToMove = state.toMove;
  state.toMove = maximizingPlayer; const myMoves = state.legalMoves().length;
  state.toMove = opponent; const oppMoves = state.legalMoves().length;
  state.toMove = currentToMove;
  let value = 0.0;
  value += 100.0 * (myPieces - oppPieces);
  value += 2.0 * (myMoves - oppMoves);
  value += 1.0 * (9 - (maximizingPlayer === PLAYER_WHITE ? state.whiteInHand : state.blackInHand));
  return value;
}

export function minimax(state, depth, alpha, beta, maximizingPlayer, useAlphaBeta){
  if(depth===0 || state.winner!==null){
    return [evaluate(state, maximizingPlayer), null];
  }
  const moves = state.legalMoves();
  if(moves.length===0){
    const clone = state.clone();
    clone.winner = -clone.toMove;
    return [evaluate(clone, maximizingPlayer), null];
  }
  let bestMove = null;
  if(state.toMove === maximizingPlayer){
    let bestVal = -Infinity;
    for(const mv of moves){
      const child = state.clone();
      child.applyMove(mv);
      const [val] = minimax(child, depth-1, alpha, beta, maximizingPlayer, useAlphaBeta);
      if(val > bestVal){ bestVal = val; bestMove = mv; }
      if(useAlphaBeta){ alpha = Math.max(alpha, bestVal); if(beta <= alpha) break; }
    }
    return [bestVal, bestMove];
  } else {
    let bestVal = Infinity;
    for(const mv of moves){
      const child = state.clone();
      child.applyMove(mv);
      const [val] = minimax(child, depth-1, alpha, beta, maximizingPlayer, useAlphaBeta);
      if(val < bestVal){ bestVal = val; bestMove = mv; }
      if(useAlphaBeta){ beta = Math.min(beta, bestVal); if(beta <= alpha) break; }
    }
    return [bestVal, bestMove];
  }
}

export function chooseMove(state, difficulty){
  const moves = state.legalMoves();
  if(moves.length===0) return null;
  if(difficulty.allowRandom && Math.random()<0.5) return moves[Math.floor(Math.random()*moves.length)];
  const [value, move] = minimax(state, difficulty.depth, -Infinity, Infinity, state.toMove, difficulty.useAlphaBeta);
  return move ?? moves[Math.floor(Math.random()*moves.length)];
}

export function hint(state, difficulty=MEDIUM){
  return chooseMove(state, difficulty);
}
