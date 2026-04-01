import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "Joe.UploadNPZ",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "JoeUploadNPZ") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
            const node = this;

            try {
                node.size = [420, 260];
            } catch (e) {
                console.warn("[JoeUploadNPZ] resize failed:", e);
            }

            const iframe = document.createElement("iframe");
            iframe.src = "/extensions/ComfyUI-HyMotion/JoeUploadNPZ.html";
            iframe.style.cssText = "width:100%; height:130px; border:0; background:#111;";

            if (typeof node.addDOMWidget === "function") {
                node.addDOMWidget("Upload NPZ", "joe_upload_npz", iframe);
            } else {
                node.html = iframe;
            }

            const getPathWidget = () => {
                const widgets = node.widgets || [];
                return widgets.find((w) => w && w.name === "npz_path") || null;
            };

            const sendPathToIframe = (pathValue) => {
                if (!iframe.contentWindow) return;
                iframe.contentWindow.postMessage(
                    {
                        type: "joe_npz_current_path",
                        npzPath: pathValue || "",
                    },
                    "*"
                );
            };

            const syncCurrentPath = () => {
                const pathWidget = getPathWidget();
                sendPathToIframe(pathWidget ? pathWidget.value : "");
            };

            window.addEventListener("message", (event) => {
                const data = event.data || {};
                if (data.type !== "joe_npz_uploaded") return;
                if (typeof data.npzPath !== "string") return;

                const pathWidget = getPathWidget();
                if (!pathWidget) return;

                pathWidget.value = data.npzPath;
                if (typeof pathWidget.callback === "function") {
                    pathWidget.callback(data.npzPath);
                }
                node.setDirtyCanvas(true, true);
                syncCurrentPath();
            });

            const origOnExecuted = node.onExecuted;
            node.onExecuted = function (output) {
                if (origOnExecuted) {
                    try {
                        origOnExecuted.apply(this, arguments);
                    } catch (e) {
                        console.warn("[JoeUploadNPZ] original onExecuted error:", e);
                    }
                }
                const ui = output?.ui || output || {};
                const uiPath = ui?.npz_path?.[0];
                if (typeof uiPath === "string") {
                    sendPathToIframe(uiPath);
                } else {
                    syncCurrentPath();
                }
            };

            setTimeout(syncCurrentPath, 200);
            return r;
        };
    },
});

