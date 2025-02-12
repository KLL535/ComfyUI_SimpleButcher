import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "Simple Load Images from Dir",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Simple Load Images from Dir") {
            const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                if (originalOnNodeCreated) { originalOnNodeCreated.call(this); }
                let counter = 0;
                const count = this.widgets.find((w) => w.name === "count");
                count.type = "converted-widget"; // hidden
                count.serializeValue = () => { return counter++; }
                api.addEventListener("promptQueued", () => { counter = 0; }); // reset
            };
        }
    },
});
