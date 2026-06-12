"use strict";
const path = require("path");
const { workspace, window } = require("vscode");
const {
  LanguageClient,
  TransportKind,
} = require("vscode-languageclient/node");

let client;

async function activate(context) {
  const config = workspace.getConfiguration("cruhon.lsp");

  if (!config.get("enabled", true)) {
    return;
  }

  // TCP mode: connect to an already-running server
  if (config.get("tcpMode", false)) {
    const port = config.get("tcpPort", 2087);
    const serverOptions = () =>
      new Promise((resolve) => {
        const net = require("net");
        const socket = net.createConnection({ port }, () => {
          resolve({ reader: socket, writer: socket });
        });
        socket.on("error", (err) => {
          window.showErrorMessage(
            `Cruhon LSP: Cannot connect to TCP server on port ${port}: ${err.message}`
          );
        });
      });

    client = new LanguageClient(
      "cruhon-lsp",
      "Cruhon Language Server",
      serverOptions,
      _clientOptions()
    );
    client.start();
    context.subscriptions.push(client);
    return;
  }

  // Stdio mode: spawn the Python server
  const pythonPath = config.get("pythonPath", "python");
  const serverOptions = {
    command: pythonPath,
    args: ["-m", "cruhon_lsp"],
    transport: TransportKind.stdio,
    options: { env: process.env },
  };

  client = new LanguageClient(
    "cruhon-lsp",
    "Cruhon Language Server",
    serverOptions,
    _clientOptions()
  );

  client.start();
  context.subscriptions.push(client);
}

function _clientOptions() {
  return {
    documentSelector: [
      { scheme: "file",      language: "cruhon" },
      { scheme: "untitled",  language: "cruhon" },
    ],
    synchronize: {
      fileEvents: workspace.createFileSystemWatcher("**/*.clpy"),
    },
  };
}

async function deactivate() {
  if (client) {
    await client.stop();
  }
}

module.exports = { activate, deactivate };
