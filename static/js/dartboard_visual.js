/**
 * Shared dartboard face renderer.
 *
 * Draws the 20 segments x 4 rings plus both bulls as SVG, in one of two modes:
 *
 *   "status"      - read-only, colours each segment by a caller-supplied status
 *                   (used by the admin zone-mapping page)
 *   "interactive" - clickable, resolving ring + segment into {score, multiplier}
 *                   (used by the game pages to correct a throw)
 *
 * Extracted from templates/admin_dartboard_testing.html so both uses share the
 * same trig and path maths.
 */
(function () {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";

  // Clockwise from the top, as on a real board
  const DARTBOARD_NUMBERS = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5];

  const CENTER = 225;
  const VIEWBOX = "0 0 450 450";

  const RADII = {
    outerDouble: 185,
    innerDouble: 170,
    outerTriple: 135,
    innerTriple: 120,
    singleInner: 16,
    bullOuter: 16,
    bullInner: 8,
  };

  const STATUS_COLORS = {
    mapped: "#4CAF50", // Green
    unmapped: "#9e9e9e", // Grey
    faulty: "#f44336", // Red - duplicate mapping
    stroke: "#333",
    text: "#000",
    bullOuter: "#D4600C",
    bullInner: "#D4A600",
  };

  // A playable board: alternating black/cream singles, red/green double+triple
  const PLAY_COLORS = {
    stroke: "#222",
    text: "#eee",
    singleDark: "#2b2b2b",
    singleLight: "#e8dcc0",
    ringDark: "#c62828",
    ringLight: "#2e7d32",
    bullOuter: "#c62828",
    bullInner: "#2e7d32",
  };

  function createSegment(svg, innerRadius, outerRadius, startAngle, endAngle, fill, colors) {
    const cx = CENTER;
    const cy = CENTER;
    const x1 = cx + innerRadius * Math.cos(startAngle);
    const y1 = cy + innerRadius * Math.sin(startAngle);
    const x2 = cx + outerRadius * Math.cos(startAngle);
    const y2 = cy + outerRadius * Math.sin(startAngle);
    const x3 = cx + outerRadius * Math.cos(endAngle);
    const y3 = cy + outerRadius * Math.sin(endAngle);
    const x4 = cx + innerRadius * Math.cos(endAngle);
    const y4 = cy + innerRadius * Math.sin(endAngle);

    const largeArc = endAngle - startAngle > Math.PI ? 1 : 0;

    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute(
      "d",
      `M ${x1} ${y1} L ${x2} ${y2} A ${outerRadius} ${outerRadius} 0 ${largeArc} 1 ${x3} ${y3} ` +
        `L ${x4} ${y4} A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${x1} ${y1} Z`
    );
    path.setAttribute("fill", fill);
    path.setAttribute("stroke", colors.stroke);
    path.setAttribute("stroke-width", "1");

    path.style.transition = "opacity 0.2s";
    path.addEventListener("mouseenter", () => {
      path.style.opacity = "0.8";
    });
    path.addEventListener("mouseleave", () => {
      path.style.opacity = "1";
    });

    svg.appendChild(path);
    return path;
  }

  function createCircle(svg, radius, fill, colors) {
    const circle = document.createElementNS(SVG_NS, "circle");
    circle.setAttribute("cx", CENTER);
    circle.setAttribute("cy", CENTER);
    circle.setAttribute("r", radius);
    circle.setAttribute("fill", fill);
    circle.setAttribute("stroke", colors.stroke);
    circle.setAttribute("stroke-width", "2");
    svg.appendChild(circle);
    return circle;
  }

  function createLabel(svg, num, midRad, colors) {
    const labelRadius = 205;
    const text = document.createElementNS(SVG_NS, "text");
    text.setAttribute("x", CENTER + labelRadius * Math.cos(midRad));
    text.setAttribute("y", CENTER + labelRadius * Math.sin(midRad));
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("dy", "0.3em");
    text.setAttribute("fill", colors.text);
    text.setAttribute("font-size", "16");
    text.setAttribute("font-weight", "bold");
    text.style.pointerEvents = "none";
    text.textContent = num;
    svg.appendChild(text);
  }

  function createSvg(size) {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", VIEWBOX);
    svg.setAttribute("width", size);
    svg.setAttribute("height", size);
    svg.style.maxWidth = "100%";
    return svg;
  }

  /**
   * Render the board.
   *
   * @param {HTMLElement} container Element to render into (its content is replaced)
   * @param {Object} options
   *   mode        "status" (default) or "interactive"
   *   size        Pixel size of the square SVG, default 350
   *   getStatus   (zone, multiplier) => status key, for mode "status"
   *   onSelect    ({score, multiplier}) => void, for mode "interactive"
   */
  function render(container, options) {
    const opts = options || {};
    const interactive = opts.mode === "interactive";
    const colors = interactive ? PLAY_COLORS : STATUS_COLORS;
    const getStatus = opts.getStatus || (() => "unmapped");
    const svg = createSvg(opts.size || 350);

    function fillFor(zone, multiplier, index, ring) {
      if (!interactive) return colors[getStatus(zone, multiplier)] || colors.unmapped;
      const light = index % 2 === 0;
      if (ring === "single") return light ? colors.singleLight : colors.singleDark;
      return light ? colors.ringLight : colors.ringDark;
    }

    function addSegment(inner, outer, startRad, endRad, zone, multiplier, index, ring) {
      const path = createSegment(
        svg,
        inner,
        outer,
        startRad,
        endRad,
        fillFor(zone, multiplier, index, ring),
        colors
      );
      if (interactive && opts.onSelect) {
        path.style.cursor = "pointer";
        path.addEventListener("click", () => opts.onSelect({ score: zone, multiplier }));
      }
      return path;
    }

    DARTBOARD_NUMBERS.forEach((num, index) => {
      const startAngle = (index - 0.5) * (360 / 20) - 90;
      const endAngle = (index + 0.5) * (360 / 20) - 90;
      const startRad = (startAngle * Math.PI) / 180;
      const endRad = (endAngle * Math.PI) / 180;

      // Outward from the centre: inner single, triple, outer single, double
      addSegment(RADII.singleInner, RADII.innerTriple, startRad, endRad, num, "SINGLE", index, "single");
      addSegment(RADII.innerTriple, RADII.outerTriple, startRad, endRad, num, "TRIPLE", index, "ring");
      addSegment(RADII.outerTriple, RADII.innerDouble, startRad, endRad, num, "SINGLE", index, "single");
      addSegment(RADII.innerDouble, RADII.outerDouble, startRad, endRad, num, "DOUBLE", index, "ring");

      createLabel(svg, num, ((startAngle + endAngle) / 2 / 180) * Math.PI, colors);
    });

    // Outer border
    const border = document.createElementNS(SVG_NS, "circle");
    border.setAttribute("cx", CENTER);
    border.setAttribute("cy", CENTER);
    border.setAttribute("r", 190);
    border.setAttribute("fill", "none");
    border.setAttribute("stroke", colors.stroke);
    border.setAttribute("stroke-width", "4");
    svg.appendChild(border);

    // Outer bull (25) then inner bull (50)
    const bullFill = interactive ? colors.bullOuter : colors[getStatus(25, "BULL")] || colors.bullOuter;
    const bull = createCircle(svg, RADII.bullOuter, bullFill, colors);

    const dblBullFill = interactive
      ? colors.bullInner
      : colors[getStatus(25, "DBLBULL")] || colors.bullInner;
    const dblBull = createCircle(svg, RADII.bullInner, dblBullFill, colors);

    if (interactive && opts.onSelect) {
      bull.style.cursor = "pointer";
      bull.addEventListener("click", () => opts.onSelect({ score: 25, multiplier: "BULL" }));
      dblBull.style.cursor = "pointer";
      dblBull.addEventListener("click", () => opts.onSelect({ score: 25, multiplier: "DBLBULL" }));
    }

    container.innerHTML = "";
    container.appendChild(svg);
    return svg;
  }

  window.DartboardVisual = { render, DARTBOARD_NUMBERS, STATUS_COLORS, RADII };
})();
