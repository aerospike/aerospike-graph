// Handles routing to the different queries

import {select1El, select2El, updateSelectRefs} from "./state.js";
import {drawGraph} from "./d3Graph.js"
import {addListeners} from "./autocompleteSelect.js";
import {getState, setState} from "./state.js";

function userSelectHTML(selectId, datalistId, defaultValue = "") {
    return `
    <input
      id="${selectId}"
      list="${datalistId}"
      placeholder="Type a user name…"
    />
    <datalist id="${datalistId}"></datalist>
  `;
}

// Feeds state values then calls for graph data and parses
export async function getGraph() {
    const val1 = select1El?.value;
    const val2 = select2El?.value;
    const key = location.hash.slice(1) || 'between';

    const params = new URLSearchParams({
        routeKey: key,
        user1: val1,
        user2: val2
    });
    const resp = await fetch(`/graph?${params}`);

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const jsonData = await resp.json();
    let {nodes, links: rawLinks, state, stateName} = jsonData;
    if(state){
        console.log(state)
        setState(stateName, state)
    }
    const links = rawLinks.map((l) => ({
        ...l, label: l.transactionId || l.type || l.label || "",
    }));
    return {nodes, links}
}

// Produces list of all usernames in the database
export async function getNames() {
    const resp = await fetch(`/names`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const jsonData = await resp.json();
    let {names} = await jsonData;
    return {names}
}

// Defines elements of each route to be used
const routes = {
    between: {
        title: 'Transactions Between Users', render: container => {
            container.innerHTML = `
        ${userSelectHTML("user-select-1", "data-list-1", "Alice")}
        ${userSelectHTML("user-select-2", "data-list-2", "Bob")}
      `;
            updateSelectRefs()
        }
    },
    incoming: {
        title: 'Incoming Transactions to User', render: container => {
            container.innerHTML = `
        ${userSelectHTML("user-select-1", "data-list-1", "Bob")}
      `;
            updateSelectRefs()
        }
    },
    outgoing: {
        title: 'Outgoing Transactions from User', render: container => {
            container.innerHTML = `
        ${userSelectHTML("user-select-1", "data-list-1", "Bob")}
      `;
            updateSelectRefs()
        }
    },
    hub: {
        title: '', render: container => {
            container.innerHTML = `
        <div id="hub-content"><h3>Detecting Fraud... </h3></div>
      `;
        }
    }
};

// Handles content updates based on route and calls to redraw the graph
async function router() {
    const hash = location.hash.slice(1) || 'between';
    const route = routes[hash] || routes.between;
    document.getElementById('query-title').textContent = route.title;

    const contentDiv = document.getElementById('nav-content');
    contentDiv.innerHTML = '';
    await route.render(contentDiv);
    addListeners();
    await drawGraph()
    if (hash === "hub") {
        const hubName = document.getElementById("hub-content");
        const {props} = getState()
        console.log(props)
        hubName.innerHTML = `
            <div id="hub-content">
              <h3>Possible Fraud Detected - ${props.name}</h3>
              <h4>Outgoing Transactions are ${props.increase}x the average</h4>
            </div>
         `;
    }
}

// Listen for hash changes and initial load
window.addEventListener('hashchange', router);
window.addEventListener('DOMContentLoaded', router);