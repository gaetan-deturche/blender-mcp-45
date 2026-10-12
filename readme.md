# Blender MCP

> **Fork for Blender 4.5 LTS** of [lab/blender_mcp](https://projects.blender.org/lab/blender_mcp)
> (upstream requires Blender 5.1+). Changes:
>
> - Add-on: `blender_version_min = "4.5.0"`; the weak sandbox hooks `bpy.ops` through
>   `_bpy_ops_submodule__getattr__` when `_op_create_function` (5.1+) is absent.
> - `data/api` and `data/manual` regenerated for Blender 4.5 (`sphinx_doc_gen.py` from tag `v4.5.13`,
>   manual branch `blender-v4.5-release`).
> - `get_blendfile_summary_missing_files` falls back to `bpy.utils.blend_paths` (no `file_path_foreach` in 4.5).
> - Windows fixes: CLI tools no longer inherit the MCP stdio pipe (hung Blender), API docs generated on
>   Windows get their `literalinclude` paths normalized, and the tests run on Windows.
>
> Install: `blender --command extension build --source-dir=addon/blender_mcp_addon`, then install the
> zip from *Preferences > Get Extensions > Install from Disk* and enable *Allow Online Access*.
> Server: `pip install -e mcp`, then run `blender-mcp` (stdio) with `BLENDER_PATH` set to the 4.5 binary.

## Overview

A lightweight MCP (Model Context Protocol) server for Blender.
It offers a natural language interface with Blender's Python API,
improving access to documentation, and allowing users to explore
and understand complex setups.

Read the documentation at [blender.org/lab/mcp-server](https://www.blender.org/lab/mcp-server/)

----

The project is deliberately small, maintainable, and does no more than
necessary. It has two components that communicate over a TCP socket:

- A **Blender add-on** that runs inside Blender and executes requests.
- An **MCP server** that runs as a separate process, launched by the
  MCP client (e.g. [Llama.cpp](https://projects.blender.org/lab/blender_mcp/wiki/Llama.cpp)).

The data flow is:
```
MCP Client  ⇐ MCP/stdio ⇒  blender-mcp  ⇐ TCP socket ⇒  Blender Add-on
```


## Blender Add-on

Located in ``addon/blender_mcp_addon/``.

A Blender extension that allows the MCP server to communicate with a
running Blender instance. It must be installed and enabled for any of
the MCP tools to work.

The add-on provides a preferences panel for configuring the host, port,
and an optional auto-start setting.

### Functionality Overview

Note that this is intended to be a fairly minimal add-on.

Connectivity
   - Auto-start (optional), is non-blocking any issues can be viewed from the preferences.
   - Configurable polling intervals (active and idle rates) from preferences to avoid excessive overhead.
   - Client timeout protection - stalled connections are evicted.
   - Start/stop operators accessible from the preferences panel.
   - Deferred responses are supported only by the interactive add-on server;
     background mode requires requests to complete synchronously and rejects deferred results.




## MCP Server

Located in ``mcp/blmcp/``, installed as a Python package with the
entry point ``blender-mcp``.

An MCP client launches this process and communicates with it over
stdio. The server connects to the add-on's TCP socket to relay
requests to Blender.

``mcp/blmcp/data/``
   Data files bundled with the package.

   - ``prompts.yml`` provides instructions sent to the LLM at
     connection time.
   - ``api/`` contains Blender Python API reference in RST format.
   - ``manual/`` contains Blender user manual excerpts in RST format.

``mcp/blmcp/tools/``
   Each tool is a single module, auto-discovered at startup.
   Modules ending in ``_toolcode`` contain code that runs inside
   Blender (sent to the add-on for execution) and are skipped during
   discovery.

``mcp/blmcp/tools_helpers/``
   Shared utilities used by tools. Tools should not import from each
   other; shared logic lives here instead.


### Tools

See [readme_tools.rst](readme_tools.rst) for the tools the MCP server exposes.
