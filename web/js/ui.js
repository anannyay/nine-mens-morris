import { POINTS_NORM, PLAYER_WHITE, PLAYER_BLACK, EMPTY, ADJACENT } from './constants.js';
import { Move } from './state.js';
import { chooseMove, hint as aiHint, EASY, MEDIUM, HARD } from './ai.js';

function createSVG(tag, attrs={}){
  const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for(const [k,v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
}

export class GameUI{
  constructor(state, mount){
    this.state = state;
    this.mount = mount;
    this.width = 1000; this.height = 1000;
    this.aiEnabled = false; this.aiColor = PLAYER_BLACK; this.difficulty = MEDIUM;
    this.selected = null; this.legalTargets = [];
    this.listeners = new Set();
    this.showHint = false; this.hintMove = null;
    this.svg = null; this.piecesLayer = null;
    this._setup();
  }
  onChange(fn){ this.listeners.add(fn); return () => this.listeners.delete(fn); }
  emitChange(){ for(const fn of this.listeners) fn(); }
  setAIEnabled(v){ this.aiEnabled = v; this.emitChange(); }
  setAIColor(c){ this.aiColor = c; this.emitChange(); }
  setAIDifficulty(d){ this.difficulty = d; this.emitChange(); }
  toggleHint(){ this.showHint = !this.showHint; if(!this.showHint) this.hintMove=null; this.render(); }
  clearSelections(){ this.selected=null; this.legalTargets=[]; this.hintMove=null; }

  _setup(){
    this.mount.innerHTML = '';
    const svg = createSVG('svg', { class: 'board-svg', viewBox: '0 0 1000 1000' });
    this.svg = svg;
    const edgesLayer = createSVG('g');
    const pointsLayer = createSVG('g');
    const piecesLayer = createSVG('g');
    this.piecesLayer = piecesLayer;

    // Edges from ADJACENT
    for(let i=0;i<24;i++){
      for(const j of ADJACENT[i]){
        if(j>i){
          const [x1,y1] = this._pointPx(i); const [x2,y2] = this._pointPx(j);
          edgesLayer.appendChild(createSVG('line', { class:'edge', x1,y1,x2,y2 }));
        }
      }
    }

    // Points
    for(let i=0;i<24;i++){
      const [cx,cy] = this._pointPx(i);
      const p = createSVG('circle', { class:'point', r:16, cx, cy, 'data-idx': i });
      p.addEventListener('click', () => this._handlePointClick(i));
      pointsLayer.appendChild(p);
    }

    svg.appendChild(edgesLayer);
    svg.appendChild(pointsLayer);
    svg.appendChild(piecesLayer);
    this.mount.appendChild(svg);

    // Drag support
    svg.addEventListener('mousedown', (e) => this._onMouseDown(e));
    svg.addEventListener('mousemove', (e) => this._onMouseMove(e));
    window.addEventListener('mouseup', (e) => this._onMouseUp(e));
  }

  _pointPx(idx){
    const [nx,ny] = POINTS_NORM[idx];
    return [60 + nx * (1000-120), 60 + ny * (1000-120)];
  }

  _handlePointClick(idx){
    if(this.state.winner!==null) return;
    if(this.state.removalPending){
      const mv = new Move(this.state.toMove, null, null, idx);
      if(this.state.applyMove(mv)){
        this.selected=null; this.legalTargets=[]; this._afterMove();
      }
      return;
    }
    if(this.state.phase==='placing'){
      const mv = new Move(this.state.toMove, null, idx, null);
      if(this.state.applyMove(mv)){
        this.selected=null; this.legalTargets=[]; this._afterMove();
      }
      return;
    }
    if(this.selected===null){
      if(this.state.board[idx]===this.state.toMove){
        this.selected = idx; this._computeLegalTargets(idx);
      }
    } else {
      const fromIdx = this.selected;
      const mv = new Move(this.state.toMove, fromIdx, idx, null);
      if(this.state.applyMove(mv)){
        this.selected=null; this.legalTargets=[]; this._afterMove();
      } else if(this.state.board[idx]===this.state.toMove){
        this.selected=idx; this._computeLegalTargets(idx);
      } else {
        this.selected=null; this.legalTargets=[];
      }
    }
    this.render();
  }

  _computeLegalTargets(fromIdx){
    this.legalTargets = [];
    for(const mv of this.state.legalMoves()){
      if(mv.fromIdx===fromIdx && mv.toIdx!==null) this.legalTargets.push(mv.toIdx);
    }
  }

  _onMouseDown(e){
    if(this.state.phase==='placing' || this.state.removalPending || this.state.winner!==null) return;
    const idx = this._hitPoint(e);
    if(idx!==null && this.state.board[idx]===this.state.toMove){
      this.selected = idx; this._computeLegalTargets(idx); this.render();
    }
  }
  _onMouseMove(e){
    // could draw ghost piece while dragging in future
  }
  _onMouseUp(e){
    if(this.selected===null) return;
    const idx = this._hitPoint(e);
    if(idx!==null){
      const mv = new Move(this.state.toMove, this.selected, idx, null);
      if(this.state.applyMove(mv)){ this.selected=null; this.legalTargets=[]; this._afterMove(); this.render(); return; }
    }
    this.selected=null; this.legalTargets=[]; this.render();
  }
  _hitPoint(e){
    const pt = this.svg.createSVGPoint(); pt.x = e.offsetX; pt.y = e.offsetY;
    // hit test by distance to each point
    for(let i=0;i<24;i++){
      const [cx,cy] = this._pointPx(i);
      const dx = pt.x-cx, dy=pt.y-cy; if(Math.hypot(dx,dy) <= 22) return i;
    }
    return null;
  }

  _afterMove(){
    for(const ev of this.state.events){
      if(ev.type==='formed_mill'){ this._toast('Mill formed! Remove an opponent piece.'); this._pulseTargets(); }
      if(ev.type==='game_over'){
        this._celebrate(ev.winner);
      }
    }
    this.emitChange();
    this.maybeAIMove();
  }

  maybeAIMove(){
    if(!this.aiEnabled) return;
    if(this.state.winner!==null) return;
    if(this.state.toMove!==this.aiColor) return;
    const mv = chooseMove(this.state, this.difficulty);
    if(mv){ this.state.applyMove(mv); this.emitChange(); this.render(); }
  }

  setToastContainer(){
    if(!this.toast){ this.toast = document.createElement('div'); this.toast.className='toast'; this.mount.appendChild(this.toast); }
  }
  _toast(msg){ this.setToastContainer(); this.toast.textContent = msg; clearTimeout(this.toastTimer); this.toastTimer = setTimeout(()=>{ this.toast.remove(); this.toast=null; }, 2000); }

  _pulseTargets(){
    // add a brief class to highlight target points
    const points = this.svg.querySelectorAll('circle.point');
    points.forEach(p => { p.classList.remove('target'); });
  }

  _celebrate(winner){
    const container = document.getElementById('confettiContainer');
    for(let i=0;i<120;i++){
      const el = document.createElement('div');
      el.className='confetti';
      const hue = winner===PLAYER_WHITE ? 210 : 0;
      el.style.background = `hsl(${hue + Math.random()*30}, 90%, ${50 + Math.random()*20}%)`;
      el.style.left = Math.random()*100 + 'vw';
      el.style.animation = `confetti-fall ${2+Math.random()*2}s linear ${Math.random()*0.6}s forwards`;
      container.appendChild(el);
      setTimeout(()=> el.remove(), 4000);
    }
    this._toast(winner===PLAYER_WHITE ? 'White wins!' : 'Black wins!');
  }

  render(){
    // Points styling
    const pointEls = this.svg.querySelectorAll('circle.point');
    pointEls.forEach((p) => {
      const idx = Number(p.getAttribute('data-idx'));
      p.classList.toggle('selected', this.selected===idx);
      p.classList.toggle('target', this.legalTargets.includes(idx) || (this.state.phase==='placing' && this.state.board[idx]===EMPTY));
    });

    // Pieces
    this.piecesLayer.innerHTML = '';
    for(let i=0;i<24;i++){
      const v = this.state.board[i]; if(v===EMPTY) continue;
      const [cx,cy] = this._pointPx(i);
      const piece = createSVG('circle', { class: 'piece ' + (v===PLAYER_WHITE?'white':'black'), r:13, cx, cy });
      this.piecesLayer.appendChild(piece);
    }

    // Hint arrow
    if(this.showHint){
      this.hintMove = aiHint(this.state, this.difficulty);
      if(this.hintMove && this.hintMove.toIdx!==null){
        const from = this.hintMove.fromIdx ?? this.hintMove.toIdx;
        const to = this.hintMove.toIdx;
        const [x1,y1] = this._pointPx(from); const [x2,y2] = this._pointPx(to);
        const arrow = createSVG('line', { x1, y1, x2, y2, stroke: '#ffd700', 'stroke-width': 6, 'stroke-linecap':'round' });
        this.piecesLayer.appendChild(arrow);
      }
    }
  }
}
