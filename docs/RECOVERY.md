# Recuperación

Revisa `./uninstall.sh --dry-run` y después ejecuta `./uninstall.sh`. Se restauran los archivos previos. Los archivos administrados editados por el usuario se conservan y quedan guardados en el respaldo privado bajo `$XDG_STATE_HOME/bosh-to-the-basic` (por defecto `~/.local/state/bosh-to-the-basic`). Si una operación se interrumpe, repite la orden normal para que el journal intente revertirla. Si detecta cambios concurrentes, detente y conserva el estado privado para recuperación manual.
