import { MILLS, ADJACENT, EMPTY } from './constants.js';

export function positionsInMill(board, idx){
  const player = board[idx];
  if(player === EMPTY) return null;
  for(const [a,b,c] of MILLS){
    if((idx===a||idx===b||idx===c) && board[a]===player && board[b]===player && board[c]===player){
      return [a,b,c];
    }
  }
  return null;
}

export function formsMill(board, idx, player){
  for(const [a,b,c] of MILLS){
    if(idx===a || idx===b || idx===c){
      const line = [a,b,c];
      const othersOk = line.filter(p => p!==idx).every(p => board[p]===player);
      if(othersOk) return true;
    }
  }
  return false;
}

export function legalRemovals(board, opponent){
  const oppPositions = [];
  for(let i=0;i<board.length;i++) if(board[i]===opponent) oppPositions.push(i);
  if(oppPositions.length===0) return [];
  const notInMill = oppPositions.filter(i => positionsInMill(board, i)===null);
  return notInMill.length ? notInMill : oppPositions;
}

export function neighborsOf(idx){
  return [...ADJACENT[idx]];
}
