/* Renderizador Markdown mínimo y seguro para los documentos internos.
   No usa librerías externas: escapa el HTML y luego aplica solo las marcas
   que necesitan los documentos de compras (títulos, listas, tablas, etc.). */
(function (global) {
  "use strict";

  function escapar(texto) {
    return String(texto == null ? "" : texto)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function inline(texto) {
    let salida = texto;
    salida = salida.replace(/`([^`]+)`/g, "<code>$1</code>");
    salida = salida.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    salida = salida.replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>");
    return salida;
  }

  function esSeparadorTabla(linea) {
    return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(linea);
  }

  function celdas(linea) {
    let limpia = linea.trim();
    if (limpia.startsWith("|")) limpia = limpia.slice(1);
    if (limpia.endsWith("|")) limpia = limpia.slice(0, -1);
    return limpia.split("|").map(function (celda) { return celda.trim(); });
  }

  function render(markdown) {
    const lineas = escapar(markdown)
      .replace(/\r\n?/g, "\n")
      .split("\n");
    const salida = [];
    let parrafo = [];
    let lista = null;
    let enCita = false;

    function cerrarParrafo() {
      if (parrafo.length) {
        salida.push("<p>" + inline(parrafo.join(" ")) + "</p>");
        parrafo = [];
      }
    }
    function cerrarLista() {
      if (lista) {
        salida.push("</" + lista + ">");
        lista = null;
      }
    }
    function cerrarCita() {
      if (enCita) {
        salida.push("</blockquote>");
        enCita = false;
      }
    }
    function cerrarBloques() {
      cerrarParrafo();
      cerrarLista();
      cerrarCita();
    }

    for (let i = 0; i < lineas.length; i += 1) {
      const linea = lineas[i];
      const limpia = linea.trim();

      if (!limpia) {
        cerrarParrafo();
        cerrarLista();
        cerrarCita();
        continue;
      }

      // Bloque de código
      if (limpia.startsWith("```")) {
        cerrarBloques();
        const codigo = [];
        i += 1;
        while (i < lineas.length && !lineas[i].trim().startsWith("```")) {
          codigo.push(lineas[i]);
          i += 1;
        }
        salida.push("<pre><code>" + codigo.join("\n") + "</code></pre>");
        continue;
      }

      // Tabla: encabezado + línea separadora
      if (
        limpia.includes("|") &&
        i + 1 < lineas.length &&
        esSeparadorTabla(lineas[i + 1])
      ) {
        cerrarBloques();
        const encabezados = celdas(limpia);
        i += 1;
        const filas = [];
        while (
          i + 1 < lineas.length &&
          lineas[i + 1].trim() &&
          lineas[i + 1].includes("|") &&
          !esSeparadorTabla(lineas[i + 1])
        ) {
          i += 1;
          filas.push(celdas(lineas[i]));
        }
        let tabla = '<div class="tabla-doc"><table><thead><tr>';
        encabezados.forEach(function (celda) {
          tabla += "<th>" + inline(celda) + "</th>";
        });
        tabla += "</tr></thead><tbody>";
        filas.forEach(function (fila) {
          tabla += "<tr>";
          encabezados.forEach(function (_, indice) {
            tabla += "<td>" + inline(fila[indice] || "") + "</td>";
          });
          tabla += "</tr>";
        });
        tabla += "</tbody></table></div>";
        salida.push(tabla);
        continue;
      }

      // Títulos (#, ##, ###...)
      const titulo = limpia.match(/^(#{1,6})\s+(.*)$/);
      if (titulo) {
        cerrarBloques();
        const nivel = Math.min(6, titulo[1].length + 1);
        salida.push(
          "<h" + nivel + ">" + inline(titulo[2]) + "</h" + nivel + ">"
        );
        continue;
      }

      // Separador horizontal
      if (/^([-*_])\1{2,}$/.test(limpia)) {
        cerrarBloques();
        salida.push("<hr>");
        continue;
      }

      // Cita
      if (/^>\s?/.test(limpia)) {
        cerrarParrafo();
        cerrarLista();
        if (!enCita) {
          salida.push("<blockquote>");
          enCita = true;
        }
        salida.push("<p>" + inline(limpia.replace(/^>\s?/, "")) + "</p>");
        continue;
      }

      // Lista con viñetas
      const vineta = limpia.match(/^[-*+]\s+(.*)$/);
      if (vineta) {
        cerrarParrafo();
        cerrarCita();
        if (lista !== "ul") {
          cerrarLista();
          salida.push("<ul>");
          lista = "ul";
        }
        salida.push("<li>" + inline(vineta[1]) + "</li>");
        continue;
      }

      // Lista numerada
      const numerada = limpia.match(/^\d+[.)]\s+(.*)$/);
      if (numerada) {
        cerrarParrafo();
        cerrarCita();
        if (lista !== "ol") {
          cerrarLista();
          salida.push("<ol>");
          lista = "ol";
        }
        salida.push("<li>" + inline(numerada[1]) + "</li>");
        continue;
      }

      // Párrafo (las líneas consecutivas se unen como en Markdown)
      cerrarLista();
      cerrarCita();
      parrafo.push(limpia);
    }

    cerrarBloques();
    return salida.join("\n");
  }

  global.MarkdownCompras = { render: render };
  if (typeof module !== "undefined" && module.exports) {
    module.exports = { render: render };
  }
})(typeof window !== "undefined" ? window : globalThis);
