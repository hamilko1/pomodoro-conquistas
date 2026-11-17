(function () {
  "use strict";

  const raiz = document.getElementById("timer");
  if (!raiz) return;

  const URL_INICIAR = raiz.dataset.urlIniciar;
  const URL_CONCLUIR = raiz.dataset.urlConcluir; // contém /0/ no lugar do id
  const CSRF = document.querySelector('meta[name="csrf-token"]').content;
  const CHAVE_ESTADO = "pomodoro.estado";
  const CHAVE_DURACOES = "pomodoro.duracoes";
  const FOCOS_ATE_PAUSA_LONGA = 4;
  const ROTULOS = { foco: "Foco", pausa_curta: "Pausa curta", pausa_longa: "Pausa longa" };
  const CIRCUNFERENCIA = 2 * Math.PI * 90;

  const tempoEl = document.getElementById("tempo");
  const anelEl = document.getElementById("anel");
  const msgEl = document.getElementById("mensagem");
  const btnPrincipal = document.getElementById("btn-principal");
  const btnCancelar = document.getElementById("btn-cancelar");
  const materiaEl = document.getElementById("materia");
  const botoesTipo = Array.from(raiz.querySelectorAll(".tipo"));
  const camposDuracao = Array.from(raiz.querySelectorAll("input[data-tipo]"));

  let duracoes = { foco: 25, pausa_curta: 5, pausa_longa: 15 };
  let focosHoje = Number(raiz.dataset.focosHoje) || 0;
  // fase: parado | rodando | pausado | concluindo
  let e = { fase: "parado", tipo: "foco", sessaoId: null, totalMs: 0, fimEm: 0, restanteMs: 0 };
  let intervalo = null;

  // ---------- Gerenciador de Áudio com Web Audio API (Aprimorado) ----------
  let audioCtx = null;

  function getAudioContext() {
    if (!audioCtx) {
      const ContextoAudio = window.AudioContext || window.webkitAudioContext;
      if (ContextoAudio) audioCtx = new ContextoAudio();
    }
    if (audioCtx && audioCtx.state === "suspended") {
      audioCtx.resume();
    }
    return audioCtx;
  }

  // Som de clique sutil para interatividade dos botões
  function playClickSound() {
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(600, ctx.currentTime);
      gain.gain.setValueAtTime(0.02, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.03);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.03);
    } catch (_) { /* áudio ignorado se bloqueado pelo navegador */ }
  }

  // Alerta sonoro ajustado (Mais audível e claro - Correção Falha Gabriel Rocha)
  function playAlarmSound() {
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.type = 'triangle'; // Onda triangular traz mais corpo e audibilidade em ruídos
      osc.frequency.setValueAtTime(523.25, now);       // Nota C5
      osc.frequency.setValueAtTime(783.99, now + 0.15); // Nota G5
      osc.frequency.setValueAtTime(1046.50, now + 0.3); // Nota C6
      
      gain.gain.setValueAtTime(0.20, now); // Ganho otimizado para ambientes com fone/ruído
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.6);
    } catch (_) { /* falhas de áudio tratadas */ }
  }

  // Jingle comemorativo para novas conquistas desbloqueadas
  function playAchievementSound() {
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const now = ctx.currentTime;
      const notes = [523.25, 659.25, 783.99, 1046.50]; // Acorde alegre
      
      notes.forEach((freq, index) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now + (index * 0.08));
        
        gain.gain.setValueAtTime(0.12, now + (index * 0.08));
        gain.gain.exponentialRampToValueAtTime(0.001, now + (index * 0.08 + 0.25));
        
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + (index * 0.08));
        osc.stop(now + (index * 0.08 + 0.25));
      });
    } catch (_) {}
  }

  // ---------- armazenamento local (conveniência; falhas são ignoradas) ----------
  function lerJson(chave) {
    try { return JSON.parse(localStorage.getItem(chave)); } catch (_) { return null; }
  }
  function salvarJson(chave, valor) {
    try { localStorage.setItem(chave, JSON.stringify(valor)); } catch (_) { /* sem armazenamento */ }
  }
  function apagar(chave) {
    try { localStorage.removeItem(chave); } catch (_) { /* sem armazenamento */ }
  }
  function salvarEstado() { salvarJson(CHAVE_ESTADO, e); }

  // ---------- tempo ----------
  function minutosDoTipo(tipo) { return duracoes[tipo] * 60000; }

  function restanteAtual() {
    if (e.fase === "rodando") return Math.max(0, e.fimEm - Date.now());
    if (e.fase === "pausado") return e.restanteMs;
    if (e.fase === "concluindo") return 0;
    return minutosDoTipo(e.tipo);
  }

  function formatar(ms) {
    const s = Math.ceil(ms / 1000);
    const mm = String(Math.floor(s / 60)).padStart(2, "0");
    const ss = String(s % 60).padStart(2, "0");
    return mm + ":" + ss;
  }

  function mostrarMensagem(texto) { msgEl.textContent = texto || ""; }

  // ---------- tela ----------
  function render() {
    const restante = restanteAtual();
    const total = e.fase === "parado" ? restante : e.totalMs;
    const progresso = total > 0 ? 1 - restante / total : 0;
    const ativo = e.fase !== "parado";

    tempoEl.textContent = formatar(restante);
    anelEl.style.strokeDashoffset = String(CIRCUNFERENCIA * (1 - progresso));
    document.title = (e.fase === "rodando" || e.fase === "pausado")
      ? formatar(restante) + " · " + ROTULOS[e.tipo]
      : "Painel · Pomodoro com Conquistas";

    botoesTipo.forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.tipo === e.tipo));
      b.disabled = ativo;
    });
    camposDuracao.forEach(function (c) { c.disabled = ativo; });
    materiaEl.disabled = ativo;

    btnPrincipal.disabled = e.fase === "concluindo";
    btnPrincipal.textContent =
      e.fase === "rodando" ? "Pausar" : e.fase === "pausado" ? "Retomar" : "Iniciar";
    btnCancelar.hidden = !(e.fase === "rodando" || e.fase === "pausado");
  }

  function iniciarTick() {
    pararTick();
    intervalo = setInterval(tick, 250);
    tick();
  }
  function pararTick() {
    if (intervalo !== null) { clearInterval(intervalo); intervalo = null; }
  }
  function tick() {
    if (e.fase !== "rodando") return;
    if (Date.now() >= e.fimEm) finalizar(); else render();
  }

  // ---------- comunicação com o servidor ----------
  async function api(url, corpo) {
    const resposta = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF },
      body: JSON.stringify(corpo || {}),
    });
    let dados = {};
    try { dados = await resposta.json(); } catch (_) { /* resposta sem JSON */ }
    if (!resposta.ok) {
      const erro = new Error(dados.erro || "Não foi possível completar a ação.");
      erro.status = resposta.status;
      throw erro;
    }
    return dados;
  }

  const esperar = function (ms) { return new Promise(function (ok) { setTimeout(ok, ms); }); };

  // ---------- ações ----------
  async function iniciar() {
    pedirPermissaoDeAviso();
    getAudioContext(); // Inicializa contexto de áudio na primeira interação do usuário
    btnPrincipal.disabled = true;
    mostrarMensagem("");
    const minutos = duracoes[e.tipo];
    try {
      const dados = await api(URL_INICIAR, {
        tipo: e.tipo,
        duracao_min: minutos,
        materia_id: materiaEl.value ? Number(materiaEl.value) : null,
      });
      e.sessaoId = dados.id;
      e.totalMs = minutos * 60000;
      e.fimEm = Date.now() + e.totalMs;
      e.fase = "rodando";
      salvarEstado();
      iniciarTick();
    } catch (erro) {
      mostrarMensagem(erro.message);
    }
    render();
  }

  function pausar() {
    e.restanteMs = Math.max(0, e.fimEm - Date.now());
    e.fase = "pausado";
    pararTick();
    salvarEstado();
    render();
  }

  function retomar() {
    e.fimEm = Date.now() + e.restanteMs;
    e.fase = "rodando";
    salvarEstado();
    iniciarTick();
    render();
  }

  function cancelar() {
    if (!window.confirm("Cancelar este ciclo? O tempo decorrido não será contabilizado.")) return;
    pararTick();
    e.fase = "parado";
    e.sessaoId = null;
    apagar(CHAVE_ESTADO);
    mostrarMensagem("Ciclo cancelado.");
    render();
  }

  async function finalizar() {
    if (e.fase === "concluindo") return;
    const tipoConcluido = e.tipo;
    const id = e.sessaoId;
    pararTick();
    e.fase = "concluindo";
    mostrarMensagem("Registrando o ciclo...");
    render();

    let dados = null;
    let ultimoErro = null;
    for (let tentativa = 0; tentativa < 4; tentativa++) {
      try {
        dados = await api(URL_CONCLUIR.replace("/0/", "/" + id + "/"));
        break;
      } catch (erro) {
        ultimoErro = erro;
        if (erro.status === 401 || erro.status === 404) break;
        await esperar(2000);
      }
    }

    e.fase = "parado";
    e.sessaoId = null;
    apagar(CHAVE_ESTADO);

    if (dados) {
      focosHoje = dados.focos_hoje;
      document.getElementById("focos-hoje").textContent = String(dados.focos_hoje);
      document.getElementById("total-focos").textContent = String(dados.total_focos);
      if (tipoConcluido === "foco") {
        e.tipo = focosHoje % FOCOS_ATE_PAUSA_LONGA === 0 ? "pausa_longa" : "pausa_curta";
        mostrarMensagem("Foco concluído! Hora de uma " + ROTULOS[e.tipo].toLowerCase() + ".");
      } else {
        e.tipo = "foco";
        mostrarMensagem("Pausa concluída. Pronto para o próximo foco?");
      }
      const extras = [];
      (dados.metas_cumpridas || []).forEach(function (d) { extras.push("Meta cumprida: " + d + "."); });
      
      let temConquistaNova = false;
      (dados.conquistas_novas || []).forEach(function (c) {
        extras.push("Nova conquista: " + c.icone + " " + c.nome + "!");
        temConquistaNova = true;
      });

      if (extras.length) mostrarMensagem(msgEl.textContent + " " + extras.join(" "));
      
      // Dispara os alertas sonoros corrigidos
      playAlarmSound();
      if (temConquistaNova) {
        setTimeout(playAchievementSound, 700); // Toca o jingle logo após o alarme principal
      }
      avisarNotificacao(tipoConcluido);
    } else {
      mostrarMensagem(
        (ultimoErro && ultimoErro.message) || "Não foi possível registrar o ciclo."
      );
    }
    render();
  }

  // ---------- avisos de notificação do navegador ----------
  function pedirPermissaoDeAviso() {
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }
  }

  function avisarNotificacao(tipoConcluido) {
    try {
      if ("Notification" in window && Notification.permission === "granted") {
        new Notification(ROTULOS[tipoConcluido] + " concluído", {
          body: tipoConcluido === "foco" ? "Hora de descansar." : "Hora de voltar ao foco.",
        });
      }
    } catch (_) { /* sem notificações */ }
  }

  // ---------- configuração e restauração ----------
  function carregarDuracoes() {
    const salvas = lerJson(CHAVE_DURACOES);
    if (salvas) {
      Object.keys(duracoes).forEach(function (tipo) {
        const v = Number(salvas[tipo]);
        if (Number.isInteger(v) && v >= 1 && v <= 180) duracoes[tipo] = v;
      });
    }
    camposDuracao.forEach(function (c) { c.value = duracoes[c.dataset.tipo]; });
  }

  function restaurar() {
    const s = lerJson(CHAVE_ESTADO);
    if (!s || !s.sessaoId || !ROTULOS[s.tipo]) return;
    if (s.fase === "rodando" && Number.isFinite(s.fimEm) && Number.isFinite(s.totalMs)) {
      e = { fase: "rodando", tipo: s.tipo, sessaoId: s.sessaoId, totalMs: s.totalMs, fimEm: s.fimEm, restanteMs: 0 };
      if (Date.now() >= e.fimEm) finalizar(); else iniciarTick();
    } else if (s.fase === "pausado" && Number.isFinite(s.restanteMs) && Number.isFinite(s.totalMs)) {
      e = { fase: "pausado", tipo: s.tipo, sessaoId: s.sessaoId, totalMs: s.totalMs, fimEm: 0, restanteMs: s.restanteMs };
    }
  }

  // ---------- eventos de clique e formulários ----------
  btnPrincipal.addEventListener("click", function () {
    if (e.fase === "parado") iniciar();
    else if (e.fase === "rodando") pausar();
    else if (e.fase === "pausado") retomar();
  });
  btnCancelar.addEventListener("click", cancelar);

  botoesTipo.forEach(function (b) {
    b.addEventListener("click", function () {
      if (e.fase !== "parado") return;
      e.tipo = b.dataset.tipo;
      mostrarMensagem("");
      render();
    });
  });

  camposDuracao.forEach(function (c) {
    c.addEventListener("change", function () {
      let v = Math.round(Number(c.value));
      if (!Number.isFinite(v)) v = duracoes[c.dataset.tipo];
      v = Math.min(180, Math.max(1, v));
      c.value = v;
      duracoes[c.dataset.tipo] = v;
      salvarJson(CHAVE_DURACOES, duracoes);
      render();
    });
  });

  // Adiciona som de clique global em botões para melhorar a usabilidade tátil/auditiva
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('button, .btn').forEach(button => {
      button.addEventListener('click', () => {
        playClickSound();
      });
    });
  });

  // Abas em segundo plano reduzem a frequência dos timers; ao voltar, recalcula na hora
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) tick();
  });

  carregarDuracoes();
  restaurar();
  render();
})();