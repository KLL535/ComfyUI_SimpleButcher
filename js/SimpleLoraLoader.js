import { app } from "/scripts/app.js";

app.registerExtension({ 
    name: "Simple Lora Loader", 
    async beforeRegisterNodeDef(nodeType, nodeData) { 
        if (nodeData.name === "Simple Lora Loader") { 
            const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                if (originalOnNodeCreated) { originalOnNodeCreated.call(this); }
                let counter = false;
                const count = this.widgets.find((w) => w.name === "count");
                count.type = "converted-widget"; // hidden
                count.serializeValue = () => { if (counter == true) { counter = false; return 0; } else return 1; }    
                this.addWidget("button","Update LoRA dictionary",null,() => { counter = true; },{ width: 150 });
            };
        }
    },
});