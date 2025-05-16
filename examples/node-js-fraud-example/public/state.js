//Updates and holds select states for queries

export let select1El = undefined;
export let select2El = undefined;
let state = {}

export function updateSelectRefs() {
    select1El = document.getElementById('user-select-1');
    select2El = document.getElementById('user-select-2');
}

export function getSelect1Val() {
    select1El = document.getElementById('user-select-1');
    let val = ""
    if(select1El){
        val = select1El.value
    }
    return val;

}

export function setState(stateName, props){
    state = {stateName, props}
}
export function getState(){
    return state
}