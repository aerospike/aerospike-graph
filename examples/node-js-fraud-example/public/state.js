//Updates and holds select states for queries

export let select1El = undefined;
export let select2El = undefined;

export function updateSelectRefs() {
    select1El = document.getElementById('user-select-1');
    select2El = document.getElementById('user-select-2');
}