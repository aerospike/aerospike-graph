import {getNames} from "./routes.js";

export async function addListeners() {
    const input1 = document.getElementById("user-select-1");
    const list1 = document.getElementById("data-list-1");
    const input2 = document.getElementById("user-select-2");
    const list2 = document.getElementById("data-list-2");
    const {names} = await getNames()

    if (input1 && list1) {
        input1.addEventListener("focus", () => {
            list1.innerHTML = "";
            names
                .forEach(name => {
                    const opt = document.createElement("option");
                    opt.value = name;
                    list1.append(opt);
                });
        })
        input1.addEventListener("input", () => {
            const q = input1.value.toLowerCase();

            list1.innerHTML = "";

            names
                .filter(name => name.toLowerCase().includes(q))
                .forEach(name => {
                    const opt = document.createElement("option");
                    opt.value = name;
                    list1.append(opt);
                });
        });
    }
    if(input2 && list2){
        console.log("WE ARE IN")
        input2.addEventListener("focus", () => {
            console.log("WE ARE DOING")
            list2.innerHTML = "";
            names
                .forEach(name => {
                    const opt = document.createElement("option");
                    opt.value = name;
                    list2.append(opt);
                });
        })
        input2.addEventListener("input", () => {
            const q = input2.value.toLowerCase();

            list2.innerHTML = "";

            names
                .filter(name => name.toLowerCase().includes(q))
                .forEach(name => {
                    const opt = document.createElement("option");
                    opt.value = name;
                    list2.append(opt);
                });
        });
    }
}

window.addEventListener('DOMContentLoaded', addListeners);
