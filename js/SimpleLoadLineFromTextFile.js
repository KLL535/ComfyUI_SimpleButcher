import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "Simple Load Line From Text File",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Simple Load Line From Text File") {
            const origOnNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const r = origOnNodeCreated ? origOnNodeCreated.apply(this) : undefined;
                let counter = 0;
                function find_count(w) { 
                    return w.name === "count"
                }
                const count = this.widgets.find(find_count);
                count.type = "converted-widget"; // hidden
                function do_counter() { 
                    return counter++; 
                }
                count.serializeValue = do_counter;
                function reset_counter() { 
                    counter = 0;
                }
                api.addEventListener("promptQueued", reset_counter); // reset
                return r;
            }
        }
    }
})
