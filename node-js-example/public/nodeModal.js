// grab modal elements
const modal = document.getElementById('property-modal');
const modalBody = document.getElementById('modal-body');
const modalClose = document.getElementById('modal-close');
const modalH3 = document.getElementById('modal-h3')

// fill & show
export function showNodeModal(d) {
    modalH3.textContent = "Node Properties"
    modalBody.textContent = JSON.stringify(d.data, null, 2);
    modal.classList.remove('hidden');
}

export function showEdgeModal(d) {
    const sourceNode = d.source.data
    const targetNode = d.target.data
    const edgeData = {
        data: d.data,
        sourceNode: sourceNode,
        targetNode: targetNode,
    }
    modalH3.textContent = "Edge Properties"
    modalBody.textContent = JSON.stringify(edgeData, null, 2);
    modal.classList.remove('hidden');
}

// hide
modalClose.addEventListener('click', () => {
    modal.classList.add('hidden');
});

// also hide if you click outside the content
modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.add('hidden');
});
