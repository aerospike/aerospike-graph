import {getNames} from "./routes.js";

export async function addListeners() {
    const input1 = document.getElementById("user-select-1");
    const list1 = document.getElementById("data-list-1");
    const input2 = document.getElementById("user-select-2");
    const list2 = document.getElementById("data-list-2");
    const {names} = await getNames("")

    const syncEnable = () => {
        const q = (input1?.value || '').toLowerCase();
        input2.disabled = !q;
    };
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
            const empty = q === "" || q === undefined
            if(input2){
                input2.disabled = empty;
            }
            list1.innerHTML = "";
            names
                .filter(name => name.toLowerCase().includes(q))
                .forEach(name => {
                    const opt = document.createElement("option");
                    opt.value = name;
                    list1.append(opt);
                });
        });
        syncEnable()
    }
    if(input2 && list2){
        input2.disabled = true
        input2.addEventListener("focus", () => {
            getNames(input1.value).then(namesWrapper => {
                const { names } = namesWrapper
                list2.innerHTML = "";
                names.forEach(name => {
                    const opt = document.createElement("option");
                    opt.value = name;
                    list2.append(opt);
                });
            }).catch(err => {
                console.error("Failed to load names:", err);
            });
        })
        input2.addEventListener("input", () => {
            getNames(input1.value).then(namesWrapper => {
                const { names } = namesWrapper
                const q = input2.value.toLowerCase();
                list2.innerHTML = "";
                names
                    .filter(name => name.toLowerCase().includes(q))
                    .forEach(name => {
                        const opt = document.createElement("option");
                        opt.value = name;
                        list2.append(opt);
                    })
            })
        });
    }
}

window.addEventListener('DOMContentLoaded', addListeners);
