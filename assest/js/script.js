function showTime() {
    const now = new Date();

    // Opciones de formato para incluir día, fecha, mes, año, y la hora completa.
    const options = {
        weekday: 'short', // Ej: Mié (o Wed si es locale 'en-US')
        year: 'numeric',
        month: 'short',   // Ej: Nov
        day: '2-digit',   // Ej: 05
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
        //timeZoneName: 'short' // Muestra el nombre de la zona horaria (Ej: GMT-3)
    };

    // 'es-ES' o 'es-CL' (para Chile, por ejemplo) define el idioma y formato.
    const formattedTime = now.toLocaleString('es-CL', options); 
    
    document.getElementById('currentTime').innerHTML = formattedTime;
}

// Llama a la función inmediatamente al cargar
showTime(); 

// Actualiza cada segundo
setInterval(showTime, 1000);