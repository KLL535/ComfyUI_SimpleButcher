import { app } from "/scripts/app.js";

app.registerExtension({ 
    name: "Simple Lora Loader", 
    async beforeRegisterNodeDef(nodeType, nodeData) { 
        if (nodeData.name === "Simple Lora Loader") { 
            const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                if (originalOnNodeCreated) { originalOnNodeCreated.call(this); }
                let counter = 1;
                const count = this.widgets.find((w) => w.name === "count");
                count.type = "converted-widget"; // hidden
                count.serializeValue = () => { return counter++; }    
                this.addWidget("button","Update LoRA dictionary",null,() => { counter = 0; },{ width: 150 });
            };
        }
    },
});