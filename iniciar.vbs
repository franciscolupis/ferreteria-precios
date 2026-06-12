Option Explicit

Dim oShell, oFS, scriptDir, venvDir, streamlitExe

Set oShell = CreateObject("WScript.Shell")
Set oFS    = CreateObject("Scripting.FileSystemObject")

' WScript.ScriptFullName apunta al .vbs real aunque se ejecute desde un acceso directo
scriptDir    = oFS.GetParentFolderName(WScript.ScriptFullName)
venvDir      = scriptDir & "\venv"
streamlitExe = venvDir & "\Scripts\streamlit.exe"

' ── PRIMERA VEZ: crear entorno e instalar dependencias ─────────────────────
If Not oFS.FolderExists(venvDir) Then
    MsgBox "Primera ejecuci" & Chr(243) & "n detectada." & vbCrLf & vbCrLf & _
           "Se crear" & Chr(225) & " el entorno virtual e instalar" & Chr(225) & _
           "n las dependencias." & vbCrLf & _
           "Esto puede tardar unos minutos. Hac" & Chr(233) & _
           " clic en Aceptar para continuar.", _
           vbInformation, "Ferretar" & Chr(237) & "a " & Chr(8212) & " Gesti" & Chr(243) & "n de Precios"

    oShell.Run "cmd /c python -m venv """ & venvDir & """", 1, True

    oShell.Run _
        "cmd /c call """ & venvDir & "\Scripts\activate.bat"" && " & _
        "pip install --upgrade pip -q && " & _
        "pip install -r """ & scriptDir & "\requirements.txt"" -q", _
        1, True

    MsgBox "Instalaci" & Chr(243) & "n completada correctamente.", _
           vbInformation, "Ferretar" & Chr(237) & "a " & Chr(8212) & " Gesti" & Chr(243) & "n de Precios"
End If

' ── REPARAR si streamlit.exe no existe (dependencias faltantes) ─────────────
If Not oFS.FileExists(streamlitExe) Then
    oShell.Run _
        "cmd /c call """ & venvDir & "\Scripts\activate.bat"" && " & _
        "pip install -r """ & scriptDir & "\requirements.txt"" -q", _
        1, True
End If

' ── ARRANCAR STREAMLIT (ventana minimizada en la barra de tareas) ───────────
' Usar /k para que el proceso quede vivo; la ventana queda minimizada, no en tu cara.
' Si algo falla, el usuario puede maximizar la ventana de la barra para ver el log.
Dim cmd
cmd = "cmd /k cd /d """ & scriptDir & """ && " & _
      "call """ & venvDir & "\Scripts\activate.bat"" && " & _
      "streamlit run main.py"

oShell.Run cmd, 2, False   ' 2 = minimized (queda en taskbar, no molesta)

' ── ABRIR NAVEGADOR luego de que el servidor arranque ──────────────────────
WScript.Sleep 4500
oShell.Run "http://localhost:8501"

Set oShell = Nothing
Set oFS    = Nothing

    