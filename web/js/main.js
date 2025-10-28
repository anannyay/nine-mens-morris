import { GameState } from './state.js';
import { GameUI } from './ui.js';
import { EASY, MEDIUM, HARD } from './ai.js';
import { PLAYER_WHITE, PLAYER_BLACK } from './constants.js';

function getDifficulty(value){
  switch(value){
    case 'easy': return EASY;
    case 'hard': return HARD;
    default: return MEDIUM;
  }
}

function updateSideVisibility(){
  const mode = document.getElementById('modeSelect').value;
  const group = document.getElementById('sideGroup');
  group.style.display = mode === 'ai' ? 'flex' : 'none';
}

async function bootstrap(){
  updateSideVisibility();
  const state = new GameState();
  const ui = new GameUI(state, document.getElementById('board'));

  const statusBar = document.getElementById('statusBar');
  const modeSelect = document.getElementById('modeSelect');
  const sideSelect = document.getElementById('sideSelect');
  const difficultySelect = document.getElementById('difficultySelect');
  const newGameBtn = document.getElementById('newGameBtn');
  const undoBtn = document.getElementById('undoBtn');
  const redoBtn = document.getElementById('redoBtn');
  const hintBtn = document.getElementById('hintBtn');

  function refreshUI(){
    const turn = state.toMove === PLAYER_WHITE ? 'White' : 'Black';
    const phase = state.phase + (state.removalPending ? ' (remove)' : '');
    statusBar.textContent = `Turn: ${turn} | Phase: ${phase} | W:${state.whiteInHand} B:${state.blackInHand}`;
    ui.render();
  }

  function configureAI(){
    const mode = modeSelect.value;
    const side = sideSelect.value;
    ui.setAIEnabled(mode === 'ai');
    ui.setAIDifficulty(getDifficulty(difficultySelect.value));
    ui.setAIColor(side === 'white' ? PLAYER_WHITE : PLAYER_BLACK);
    // If AI starts as white and it's their turn at fresh game, make a move
    ui.maybeAIMove();
  }

  modeSelect.addEventListener('change', () => { updateSideVisibility(); configureAI(); });
  sideSelect.addEventListener('change', configureAI);
  difficultySelect.addEventListener('change', configureAI);
  newGameBtn.addEventListener('click', () => { state.reset(); ui.clearSelections(); configureAI(); refreshUI(); });
  undoBtn.addEventListener('click', () => { if(state.undo()){ ui.clearSelections(); refreshUI(); } });
  redoBtn.addEventListener('click', () => { if(state.redo()){ ui.clearSelections(); refreshUI(); } });
  hintBtn.addEventListener('click', () => { ui.toggleHint(); });

  ui.onChange(() => { refreshUI(); });
  configureAI();
  refreshUI();
}

window.addEventListener('DOMContentLoaded', bootstrap);
