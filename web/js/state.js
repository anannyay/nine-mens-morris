import { EMPTY, PLAYER_WHITE, PLAYER_BLACK, STARTING_STONES_PER_PLAYER, ADJACENT } from './constants.js';
import { positionsInMill, formsMill, legalRemovals } from './rules.js';

export class Move{
  constructor(player, fromIdx=null, toIdx=null, removeIdx=null){
    this.player = player;
    this.fromIdx = fromIdx;
    this.toIdx = toIdx;
    this.removeIdx = removeIdx;
  }
}

export class GameState{
  constructor(){
    this.board = Array(24).fill(EMPTY);
    this.phase = 'placing';
    this.toMove = PLAYER_WHITE;
    this.whiteInHand = STARTING_STONES_PER_PLAYER;
    this.blackInHand = STARTING_STONES_PER_PLAYER;
    this.removalPending = false;
    this.winner = null;
    this.history = [];
    this.redoStack = [];
    this.events = [];
  }
  clone(){
    const g = new GameState();
    g.board = [...this.board];
    g.phase = this.phase;
    g.toMove = this.toMove;
    g.whiteInHand = this.whiteInHand;
    g.blackInHand = this.blackInHand;
    g.removalPending = this.removalPending;
    g.winner = this.winner;
    g.events = [];
    return g;
  }
  reset(){
    this.board = Array(24).fill(EMPTY);
    this.phase = 'placing';
    this.toMove = PLAYER_WHITE;
    this.whiteInHand = STARTING_STONES_PER_PLAYER;
    this.blackInHand = STARTING_STONES_PER_PLAYER;
    this.removalPending = false;
    this.winner = null;
    this.history = [];
    this.redoStack = [];
    this.events = [];
  }
  currentInHand(){
    return this.toMove === PLAYER_WHITE ? this.whiteInHand : this.blackInHand;
  }
  setCurrentInHand(v){
    if(this.toMove === PLAYER_WHITE) this.whiteInHand = v; else this.blackInHand = v;
  }
  numPieces(player){
    let n=0; for(const v of this.board) if(v===player) n++; return n;
  }
  isFlying(player){
    return this.numPieces(player) === 3 && this.phase !== 'placing';
  }
  pushHistory(){
    this.history.push([
      [...this.board], this.phase, this.toMove, this.whiteInHand, this.blackInHand, this.removalPending, this.winner
    ]);
    this.redoStack.length = 0;
  }
  undo(){
    if(this.history.length===0) return false;
    this.redoStack.push([
      [...this.board], this.phase, this.toMove, this.whiteInHand, this.blackInHand, this.removalPending, this.winner
    ]);
    const prev = this.history.pop();
    [this.board, this.phase, this.toMove, this.whiteInHand, this.blackInHand, this.removalPending, this.winner] = prev;
    return true;
  }
  redo(){
    if(this.redoStack.length===0) return false;
    this.history.push([
      [...this.board], this.phase, this.toMove, this.whiteInHand, this.blackInHand, this.removalPending, this.winner
    ]);
    const next = this.redoStack.pop();
    [this.board, this.phase, this.toMove, this.whiteInHand, this.blackInHand, this.removalPending, this.winner] = next;
    return true;
  }
  legalMoves(){
    if(this.winner!==null) return [];
    if(this.removalPending){
      const opponent = this.toMove === PLAYER_WHITE ? PLAYER_BLACK : PLAYER_WHITE;
      return legalRemovals(this.board, opponent).map(i => new Move(this.toMove, null, null, i));
    }
    if(this.phase==='placing'){
      const moves=[]; for(let i=0;i<24;i++){ if(this.board[i]===EMPTY) moves.push(new Move(this.toMove, null, i, null)); }
      return moves;
    }
    const moves=[]; const flying = this.isFlying(this.toMove);
    for(let i=0;i<24;i++){
      if(this.board[i]!==this.toMove) continue;
      if(flying){
        for(let j=0;j<24;j++) if(this.board[j]===EMPTY) moves.push(new Move(this.toMove, i, j, null));
      } else {
        for(const j of ADJACENT[i]) if(this.board[j]===EMPTY) moves.push(new Move(this.toMove, i, j, null));
      }
    }
    return moves;
  }
  applyMove(move){
    if(this.winner!==null) return false;
    this.events = [];
    const prevPhase = this.phase;
    this.pushHistory();
    if(move.removeIdx!==null && this.removalPending){
      if(this.board[move.removeIdx]===EMPTY || this.board[move.removeIdx]===this.toMove){ this.history.pop(); return false; }
      this.board[move.removeIdx] = EMPTY;
      this.removalPending = false;
      this.events.push({type:'removed', player:this.toMove, idx: move.removeIdx});
      this.toMove *= -1;
      this._updatePhaseAndWinner();
      if(this.phase!==prevPhase) this.events.push({type:'phase_change', from:prevPhase, to:this.phase});
      if(this.winner!==null) this.events.push({type:'game_over', winner:this.winner});
      return true;
    }
    if(this.phase==='placing'){
      if(move.toIdx===null || this.board[move.toIdx]!==EMPTY){ this.history.pop(); return false; }
      this.board[move.toIdx] = this.toMove;
      this.setCurrentInHand(this.currentInHand()-1);
      this.events.push({type:'placed', player:this.toMove, to:move.toIdx});
      if(formsMill(this.board, move.toIdx, this.toMove)){
        this.removalPending = true;
        this.events.push({type:'formed_mill', player:this.toMove, at:move.toIdx});
        return true;
      }
      this.toMove *= -1;
      this._updatePhaseAndWinner();
      if(this.phase!==prevPhase) this.events.push({type:'phase_change', from:prevPhase, to:this.phase});
      if(this.winner!==null) this.events.push({type:'game_over', winner:this.winner});
      return true;
    }
    // moving or flying
    if(move.fromIdx===null || move.toIdx===null){ this.history.pop(); return false; }
    if(this.board[move.fromIdx]!==this.toMove || this.board[move.toIdx]!==EMPTY){ this.history.pop(); return false; }
    if(!this.isFlying(this.toMove) && !ADJACENT[move.fromIdx].includes(move.toIdx)){ this.history.pop(); return false; }
    this.board[move.fromIdx] = EMPTY;
    this.board[move.toIdx] = this.toMove;
    this.events.push({type:'moved', player:this.toMove, from:move.fromIdx, to:move.toIdx});
    if(formsMill(this.board, move.toIdx, this.toMove)){
      this.removalPending = true;
      this.events.push({type:'formed_mill', player:this.toMove, at:move.toIdx});
      return true;
    }
    this.toMove *= -1;
    this._updatePhaseAndWinner();
    if(this.phase!==prevPhase) this.events.push({type:'phase_change', from:prevPhase, to:this.phase});
    if(this.winner!==null) this.events.push({type:'game_over', winner:this.winner});
    return true;
  }
  _updatePhaseAndWinner(){
    if(this.whiteInHand===0 && this.blackInHand===0 && this.phase==='placing' && !this.removalPending){
      this.phase = 'moving';
    }
    if(this.winner===null && !this.removalPending){
      this.winner = this._checkWinner();
    }
  }
  _checkWinner(){
    for(const player of [PLAYER_WHITE, PLAYER_BLACK]){
      const pieces = this.numPieces(player);
      if(pieces < 3 && (player===PLAYER_WHITE ? this.whiteInHand===0 : this.blackInHand===0)){
        return -player;
      }
    }
    if(this.phase!=='placing' && !this.removalPending){
      if(this.legalMoves().length===0){
        return -this.toMove;
      }
    }
    return null;
  }
}
