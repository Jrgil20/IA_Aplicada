/* Asistente de Compras · interfaz sin dependencias externas */
(function () {
  "use strict";

  const formulario = document.getElementById("formulario");
  const entrada = document.getElementById("pregunta");
  const boton = document.getElementById("enviar");
  const conversacion = document.getElementById("conversacion");
  const inicio = document.getElementById("inicio");
  const botonNueva = document.getElementById("nueva");
  const modal = document.getElementById("modal-documento");
  const modalId = document.getElementById("modal-id");
  const modalTitulo = document.getElementById("modal-titulo");
  const modalMeta = document.getElementById("modal-meta");
  const modalCuerpo = document.getElementById("modal-cuerpo");
  const modalCerrar = document.getElementById("modal-cerrar");

  let ocupado = false;
  let temporizador = null;

  function escapar(texto) {
    return String(texto == null ? "" : texto)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderRespuesta(texto) {
    let seguro = escapar(texto);
    seguro = seguro.replace(/\[\s*DOC\s*:\s*([^\]]+)\]/gi, function (_, interior) {
      return '<span class="cita">' + interior.trim() + "</span>";
    });
    seguro = seguro.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

    const lineas = seguro.split(/\n+/).map(function (l) { return l.trim(); }).filter(Boolean);
    const salida = [];
    let enLista = false;

    function cerrarLista() {
      if (enLista) { salida.push("</ul>"); enLista = false; }
    }

    lineas.forEach(function (linea) {
      const vineta = linea.match(/^[-•]\s+(.*)$/);
      const numerada = linea.match(/^\d+[.)]\s+(.*)$/);
      if (vineta || numerada) {
        if (!enLista) { salida.push("<ul>"); enLista = true; }
        salida.push("<li>" + (vineta ? vineta[1] : numerada[1]) + "</li>");
      } else {
        cerrarLista();
        salida.push("<p>" + linea + "</p>");
      }
    });
    cerrarLista();
    return salida.join("");
  }

  function renderFuentes(fuentes) {
    if (!fuentes || !fuentes.length) return "";
    const tarjetas = fuentes.map(function (f) {
      return (
        '<article class="fuente">' +
          '<div class="fuente-cabecera">' +
            '<span class="fuente-id">' + escapar(f.id) + "</span>" +
            '<span class="fuente-tipo">' + escapar(f.tipo || "Documento") + "</span>" +
          "</div>" +
          '<p class="fuente-titulo">' + escapar(f.titulo) + "</p>" +
          '<p class="fuente-seccion">' + escapar(f.seccion) + "</p>" +
          "<blockquote>" + escapar(f.fragmento) + "</blockquote>" +
          '<button class="ver-doc" type="button" data-doc="' + escapar(f.id) + '">' +
            "Ver documento completo" +
          "</button>" +
        "</article>"
      );
    }).join("");
    const cantidad = fuentes.length === 1 ? "1 fuente" : fuentes.length + " fuentes";
    return (
      '<details class="fuentes" open>' +
        "<summary>Fuentes citadas · " + cantidad + "</summary>" +
        '<div class="lista-fuentes">' + tarjetas + "</div>" +
      "</details>"
    );
  }

  function ocultarPortada() {
    if (inicio) inicio.hidden = true;
  }

  function mostrarPortada() {
    if (inicio) inicio.hidden = false;
  }

  function agregarUsuario(texto) {
    const articulo = document.createElement("article");
    articulo.className = "mensaje usuario";
    const burbuja = document.createElement("div");
    burbuja.className = "burbuja";
    burbuja.textContent = texto;
    articulo.appendChild(burbuja);
    conversacion.appendChild(articulo);
    desplazar(false);
  }

  function agregarCargando() {
    const articulo = document.createElement("article");
    articulo.className = "mensaje asistente cargando";
    articulo.setAttribute("aria-busy", "true");
    articulo.innerHTML =
      '<div class="avatar" aria-hidden="true">A</div>' +
      '<div class="burbuja">' +
        '<div class="puntos" aria-hidden="true"><span></span><span></span><span></span></div>' +
        '<span class="texto-cargando">Buscando en los documentos de compras…</span>' +
      "</div>";
    conversacion.appendChild(articulo);
    desplazar(false);

    const estado = articulo.querySelector(".texto-cargando");
    const comienzo = Date.now();
    temporizador = window.setInterval(function () {
      const segundos = Math.round((Date.now() - comienzo) / 1000);
      if (segundos < 3) {
        estado.textContent = "Buscando en los documentos de compras…";
      } else if (segundos < 12) {
        estado.textContent = "Redactando la respuesta con el modelo local…";
      } else {
        estado.textContent = "El modelo local sigue redactando… (" + segundos + " s)";
      }
    }, 900);
    return articulo;
  }

  function agregarAsistente(datos) {
    const articulo = document.createElement("article");
    articulo.className = "mensaje asistente" + (datos.negativa ? " negativa" : "");

    const aviso = datos.negativa
      ? '<div class="aviso-negativa"><span aria-hidden="true">!</span>' +
        "<span>Sin respaldo en los documentos</span></div>"
      : "";

    const fuentes = renderFuentes(datos.fuentes);
    const cantidad = datos.fuentes && datos.fuentes.length;
    const pie = cantidad
      ? cantidad + (cantidad === 1 ? " fuente citada" : " fuentes citadas")
      : "Sin fuente documental";
    const segundos = datos.ms ? (datos.ms / 1000).toFixed(1) + " s" : "";

    articulo.innerHTML =
      '<div class="avatar" aria-hidden="true">A</div>' +
      '<div class="burbuja">' +
        aviso +
        '<div class="respuesta">' + renderRespuesta(datos.respuesta) + "</div>" +
        fuentes +
        '<div class="pie-mensaje"><span>' + escapar(pie) + "</span>" +
          "<span>" + escapar(segundos) + "</span></div>" +
      "</div>";
    conversacion.appendChild(articulo);
    desplazar(false);
  }

  function agregarError(mensaje, pregunta) {
    const articulo = document.createElement("article");
    articulo.className = "mensaje asistente negativa";
    articulo.innerHTML =
      '<div class="avatar" aria-hidden="true">A</div>' +
      '<div class="burbuja">' +
        '<div class="aviso-negativa"><span aria-hidden="true">!</span>' +
        "<span>No se pudo completar la consulta</span></div>" +
        '<div class="respuesta"><p>' + escapar(mensaje) + "</p></div>" +
        '<button class="ver-doc reintentar" type="button" data-pregunta="' +
          escapar(pregunta) + '">Reintentar</button>' +
      "</div>";
    conversacion.appendChild(articulo);
    desplazar(false);
  }

  function desplazar(suave) {
    window.scrollTo({ top: document.body.scrollHeight, behavior: suave ? "smooth" : "auto" });
  }

  function ajustarAltura() {
    entrada.style.height = "auto";
    entrada.style.height = Math.min(entrada.scrollHeight, 150) + "px";
  }

  async function preguntar(texto) {
    const pregunta = (texto || "").trim();
    if (!pregunta || ocupado) return;

    ocupado = true;
    boton.disabled = true;
    entrada.disabled = true;
    ocultarPortada();
    agregarUsuario(pregunta);
    entrada.value = "";
    ajustarAltura();
    const cargando = agregarCargando();

    try {
      const respuesta = await fetch("/api/preguntar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pregunta: pregunta })
      });
      let datos = {};
      try { datos = await respuesta.json(); } catch (_) { datos = {}; }
      if (!respuesta.ok) {
        throw new Error(datos.error || "El servidor no pudo procesar la pregunta.");
      }
      cargando.remove();
      agregarAsistente(datos);
    } catch (error) {
      cargando.remove();
      agregarError(
        error.message || "No se pudo conectar con el asistente. Revisa que el servidor esté encendido.",
        pregunta
      );
    } finally {
      if (temporizador) { window.clearInterval(temporizador); temporizador = null; }
      ocupado = false;
      boton.disabled = false;
      entrada.disabled = false;
      entrada.focus();
    }
  }

  async function abrirDocumento(docId) {
    modalId.textContent = docId;
    modalTitulo.textContent = "Cargando documento…";
    modalMeta.textContent = "";
    modalCuerpo.textContent = "Un momento…";
    if (typeof modal.showModal === "function") modal.showModal();
    else modal.setAttribute("open", "");

    try {
      const respuesta = await fetch("/api/documento?id=" + encodeURIComponent(docId));
      const datos = await respuesta.json();
      if (!respuesta.ok) throw new Error(datos.error || "Documento no encontrado.");
      modalId.textContent = datos.id;
      modalTitulo.textContent = datos.titulo;
      const partes = [];
      if (datos.tipo) partes.push(datos.tipo);
      if (datos.proveedor) partes.push(datos.proveedor);
      if (datos.fecha) partes.push("Fecha: " + datos.fecha);
      if (datos.estado) partes.push(datos.estado);
      modalMeta.textContent = partes.join(" · ");
      modalCuerpo.textContent = datos.texto;
    } catch (error) {
      modalTitulo.textContent = "No se pudo abrir el documento";
      modalCuerpo.textContent = error.message || "Intenta de nuevo.";
    }
  }

  function cerrarModal() {
    if (typeof modal.close === "function") modal.close();
    else modal.removeAttribute("open");
  }

  formulario.addEventListener("submit", function (evento) {
    evento.preventDefault();
    preguntar(entrada.value);
  });

  entrada.addEventListener("input", ajustarAltura);
  entrada.addEventListener("keydown", function (evento) {
    if (evento.key === "Enter" && !evento.shiftKey) {
      evento.preventDefault();
      preguntar(entrada.value);
    }
  });

  document.querySelectorAll(".chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      preguntar(chip.getAttribute("data-pregunta"));
    });
  });

  botonNueva.addEventListener("click", function () {
    conversacion.innerHTML = "";
    mostrarPortada();
    window.scrollTo({ top: 0, behavior: "smooth" });
    entrada.focus();
  });

  conversacion.addEventListener("click", function (evento) {
    const ver = evento.target.closest(".ver-doc");
    if (!ver) return;
    if (ver.classList.contains("reintentar")) {
      preguntar(ver.getAttribute("data-pregunta"));
      return;
    }
    abrirDocumento(ver.getAttribute("data-doc"));
  });

  modalCerrar.addEventListener("click", cerrarModal);
  modal.addEventListener("click", function (evento) {
    if (evento.target === modal) cerrarModal();
  });

  ajustarAltura();
  entrada.focus();
})();
