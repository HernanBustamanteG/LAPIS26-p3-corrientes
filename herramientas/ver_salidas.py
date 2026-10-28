"""Imprime las salidas de texto de un notebook ejecutado (para revisar)."""
import sys
import nbformat
nb = nbformat.read(sys.argv[1], 4)
for i, c in enumerate(nb.cells):
    if c.cell_type != "code":
        continue
    for o in c.outputs:
        if o.output_type == "error":
            print("[%d] ERROR %s: %s" % (i, o.ename, o.evalue))
        t = o.get("text", o.get("data", {}).get("text/plain", ""))
        if t:
            print("[%d] %s" % (i, t[:int(sys.argv[2]) if len(sys.argv) > 2 else 2500]))
