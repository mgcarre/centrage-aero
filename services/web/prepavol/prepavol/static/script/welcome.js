document.querySelectorAll(".is-ad-btn").forEach(btn => {
    btn.addEventListener("click", e => {
        e.preventDefault()
        e.stopPropagation()
        btn.classList.add("is-loading")
        toggleSelectedButton(btn)
        const ad = e.target.innerText
        fetch(`/metar/${ad}`)
            .then(r => r.json())
            .catch(err => console.error(err))
            .then(r => {
                document.getElementById("metar_data").innerHTML = r.metar
                btn.classList.remove("is-loading")
            })
            .catch(err => console.error(err))
    })
})
const btnSrSs = document.getElementById("btn-sr-ss")
btnSrSs.addEventListener("click", (e) => {
    e.preventDefault()
    btnSrSs.classList.add("is-loading")
    navigator.permissions.query({ name: 'geolocation' }).then((result) => {
        if (result.state === 'granted' || result.state === 'prompt') {
            displaySrSs()
        } else {
            btnSrSs.classList.remove("is-loading")
            btnSrSs.classList.add("is-danger")
            btnSrSs.disabled = true
        }
    });
})

function toggleSelectedButton(btn) {
    document.querySelectorAll("button").forEach(button => {
        if (button !== btn) {
            button.classList.remove("is-selected", "is-info")
        } else {
            button.classList.add("is-selected", "is-info")
        }
    })
}

function displaySrSs() {
    const dt = luxon.DateTime
    navigator.geolocation.getCurrentPosition((coords) => {
        const { latitude, longitude } = coords.coords
        fetch(`https://api.sunrise-sunset.org/json?lat=${latitude}&lng=${longitude}&formatted=0`).then(r => r.json()).then(rep => {
            btnSrSs.classList.remove("is-loading")
            const { sunrise, sunset } = rep.results
            const dtSr = dt.fromISO(sunrise)
            const dtSs = dt.fromISO(sunset)
            const format = "HH'h'mm"
            document.getElementById("jr-aero").innerText = dtSr.minus({ minutes: 30 }).toFormat(format)
            document.getElementById("sr").innerText = dtSr.toFormat(format)
            document.getElementById("ss").innerText = dtSs.toFormat(format)
            document.getElementById("nt-aero").innerText = dtSs.plus({ minutes: 30 }).toFormat(format)
        })
    })
}