import { app } from "/scripts/app.js";
app.registerExtension({
	name: "Simple Load Image With Metadata",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name === "Simple Load Image With Metadata") {
			nodeData.input.required.upload = ["IMAGEUPLOAD"];
		}
	},
});