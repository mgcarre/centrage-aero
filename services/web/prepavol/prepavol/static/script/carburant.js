let avion = null
let params = null

function reset_form() {

}

function update_plane() {
  let callsign = document.querySelector("#callsign").value;
  avion = planes[callsign]
  update_element_HTML("#planetype", `${avion.planetype} - ${callsign}`)
}

function update_element_HTML(elementId, value, unit = "") {
  document.querySelector(elementId).innerHTML = `${value} ${unit}`.trim()
}

function update_branches() {
  const br_str = document.getElementById("nb_branches").value
  const br = parseInt(br_str)
  document.querySelectorAll(".my-branches").forEach((elem, index) => {
    elem.classList.remove("is-hidden")
    if (index >= br) {
      elem.classList.add("is-hidden")
    }
  })
}

// Event callbacks
const elem = new Map()
elem.set("#callsign", update_plane);
elem.set("#nb_branches", update_branches)

window.addEventListener("DOMContentLoaded", e => {
  elem.forEach((val, key) => {
    document.querySelector(key).addEventListener("change", val)
  })
  update_plane()
  update_branches()
})