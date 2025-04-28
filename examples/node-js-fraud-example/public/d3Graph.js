// Handles D3 and graph visualization logic

import {getGraph} from "./routes.js";

const btn = document.getElementById("refresh-btn");
btn.addEventListener("click", drawGraph);

const svg = d3.select("svg");
let width = window.innerWidth;
let height = window.innerHeight;
let simulation;

export async function drawGraph() {
    const {nodes, links} = await getGraph();
    svg.selectAll("*").remove();

    simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(120).strength(1))
        .force("charge", d3.forceManyBody().strength(-100))
        .force("collide", d3.forceCollide().radius(20))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .stop();

    // Tick to settle nodes before visualization
    for (let i = 0; i < 150; ++i) simulation.tick();

    const container = svg.append("g").attr("class", "graph-container");

    const counts = {};
    links.forEach(d => {
        const a = d.source.id ?? d.source;
        const b = d.target.id ?? d.target;
        const key = a < b ? `${a}|${b}` : `${b}|${a}`;
        d._pairKey = key;
        counts[key] = (counts[key] || 0) + 1;
    });

    const seen = {};
    links.forEach(d => {
        const key = d._pairKey;
        seen[key] = (seen[key] || 0) + 1;
        d._parallelIndex = seen[key];    // 1…N
        d._parallelCount = counts[key];  // N
    });

    // Draw curved <path> for each link
    const link = container.append("g")
        .attr("class", "links")
        .selectAll("path")
        .data(links)
        .join("path")
        .attr("class", "link")
        .attr("fill", "none")
        .attr("stroke", "#999");

    // Text labels bound to each path
    const linkLabels = container.append("g")
        .attr("class", "link-labels")
        .selectAll("text")
        .data(links)
        .join("text")
        .attr("class", "link-label")
        .append("textPath")
        .attr("startOffset", "50%")
        .attr("text-anchor", "middle")
        .attr("xlink:href", (_d, i) => `#linkPath${i}`)  // see note below
        .text(d => d.label);

    // Draw nodes and set movement events
    const node = container.append("g")
        .attr("class", "nodes")
        .selectAll("g")
        .data(nodes)
        .join("g")
        .call(
            d3.drag()
                .on("start", (event, d) => {
                    event.sourceEvent.stopPropagation();
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                })
                .on("drag", (event, d) => {
                    d.fx = event.x;
                    d.fy = event.y;
                })
                .on("end", (event, d) => {
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                })
        );

    node.append("circle").attr("r", 10);
    node.append("text").attr("x", 14).attr("y", 4).text(d => d.label);

    // Start the simulation
    simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links)
            .id(d => d.id)
            .distance(150).strength(1));

    simulation.on("tick", () => {
        link
            .attr("id", (_d, i) => `linkPath${i}`)   // ensure each has a unique ID
            .attr("d", d => {
                const {x: x1, y: y1} = d.source;
                const {x: x2, y: y2} = d.target;
                const dx = x2 - x1, dy = y2 - y1;
                const straightDist = Math.hypot(dx, dy);

                // Center offsets of the links and curve so they don't stack
                const offsetFactor = (d._parallelIndex - (d._parallelCount + 1) / 2);
                const curvature = 80; // tweak this for tighter/looser bows
                const radius = straightDist + offsetFactor * curvature;

                return `M${x1},${y1} A${radius},${radius} 0 0,1 ${x2},${y2}`;
            });

        node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    svg.call(d3.zoom().scaleExtent([0.1, 8])
        .on("zoom", event => container.attr("transform", event.transform)));
}

window.addEventListener("resize", () => {
    width = window.innerWidth;
    height = window.innerHeight;
    svg.attr("width", width).attr("height", height);
    // re-center forces on resize
    if (simulation) {
        simulation.force("center", d3.forceCenter(width / 2, height / 2));
        simulation.force("x", d3.forceX(width / 2).strength(0.05));
        simulation.force("y", d3.forceY(height / 2).strength(0.05));
        simulation.alpha(0.3).restart();
    }
});

document.addEventListener("DOMContentLoaded", drawGraph);