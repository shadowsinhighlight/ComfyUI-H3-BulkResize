import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

const NODE_NAME = "H3BulkReferenceResize";
const WIDGET_NAME = "output_resolutions";
const PLACEHOLDER = "(queue a prompt to see output resolutions)";

app.registerExtension({
    name: "bortevekk.h3BulkReferenceResize",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_NAME) {
            return;
        }

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

            const widget = ComfyWidgets["STRING"](
                this,
                WIDGET_NAME,
                ["STRING", { multiline: true }],
                app
            ).widget;

            widget.value = PLACEHOLDER;
            // never persisted into the workflow json
            widget.serializeValue = () => "";

            if (widget.inputEl) {
                widget.inputEl.readOnly = true;
                widget.inputEl.style.opacity = "0.8";
                widget.inputEl.style.fontFamily = "monospace";
                widget.inputEl.style.fontSize = "11px";
            }

            this.h3ReportWidget = widget;
            return result;
        };

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            const result = onExecuted ? onExecuted.apply(this, arguments) : undefined;

            const widget =
                this.h3ReportWidget ||
                (this.widgets || []).find((w) => w.name === WIDGET_NAME);

            if (widget && message && message.h3_resize_report) {
                const report = message.h3_resize_report;
                widget.value = Array.isArray(report) ? report.join("\n") : String(report);
                app.graph.setDirtyCanvas(true, false);
            }

            return result;
        };
    },
});
