import {userNames} from "./consts.js";

const input2 = document.getElementById("user-select-2");
const list2 = document.getElementById("data-list-2");

function addListeners() {
    const input1 = document.getElementById("user-select-1");
    const list1 = document.getElementById("data-list-1");

    input1.addEventListener("input", () => {
        const q = input1.value.toLowerCase();
        console.log("INPUT")
        // clear old options
        list1.innerHTML = "";

        // filter & keep top 10 matches
        userNames
            .filter(name => name.toLowerCase().includes(q))
            .slice(0, 10)
            .forEach(name => {
                const opt = document.createElement("option");
                opt.value = name;
                list1.append(opt);
            });
        console.log(userNames)
    });
}

window.addEventListener('DOMContentLoaded', addListeners);
