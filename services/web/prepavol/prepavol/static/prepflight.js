$(document).ready(function () {
  let callsign;
  let bew = 0;
  let frontweight = 0;
  let rearweight = 0;
  let bagweight = 0;
  let bagweight2 = 0;
  let mainfuelweight = 0;
  let wingfuelweight = 0;
  let auxfuelweight = 0;
  let auw;
  let bemoment = 0;
  let frontmoment = 0;
  let rearmoment = 0;
  let bagmoment = 0;
  let bagmoment2 = 0;
  let mainfuelmoment = 0;
  let wingfuelmoment = 0;
  let auxfuelmoment = 0;
  let moment;
  let cg;
  let essence;

  function reset_form() {
    console.log("IN RESET");
    var selectfields = [
      "#pax0",
      "#pax1",
      "#pax2",
      "#pax3",
      "#baggage",
      "#baggage2",
      "#mainfuel",
      "#leftwingfuel",
      "#rightwingfuel",
      "#auxfuel",
    ];
    $.each(selectfields, function (index, value) {
      $(value).get(0).selectedIndex = 0;
      $(value).trigger("change");
      console.log($(value).val());
    });
  }

  function update_totals() {
    auw = [
      bew,
      frontweight,
      rearweight,
      bagweight,
      bagweight2,
      mainfuelweight,
      wingfuelweight,
      auxfuelweight,
    ].reduce((a, b) => a + b);
    console.log("IN UPDATE TOTALS", mainfuelweight, auw);
    moment = [
      bemoment,
      frontmoment,
      rearmoment,
      bagmoment,
      bagmoment2,
      mainfuelmoment,
      wingfuelmoment,
      auxfuelmoment,
    ].reduce((a, b) => a + b);
    cg = moment / auw;

    $("#auw").html(auw.toFixed(1) + "kg");
    $("#cg").html(cg.toFixed(2) + "m");
    $("#moment").html(moment.toFixed(0) + "kg.m");
  }

  async function update_plane() {
    callsign = $("#callsign").val();
    plane = planes[callsign];
    console.log("IN UPDATE PLANE", plane);

    req = await fetch(`essence?type=${plane.fuel_name}`)
    essence = await req.json()
    planetype = plane.planetype;
    bew = plane.bew;
    bearm = plane.arms.bew;
    bemoment = bew * bearm;

    $("#planetype").html(planetype);
    $("#bew").html(bew.toFixed(0) + "kg");
    $("#bearm").html(bearm.toFixed(2) + "m");
    $("#bemoment").html(bemoment.toFixed(0) + "kg.m");

    update_front();
    update_rear();
    update_mainfuel();
    update_wingfuel();
    update_auxfuel();
    update_baggage();
    update_baggage2();
    update_totals();
  }

  function update_front() {
    console.log("FRONT PAX", plane); //.arms.front);
    var w1 = parseInt($("#pax0").val());
    var w2 = parseInt($("#pax1").val());

    if (w1 > 0) {
      $(".errors").empty();
    }
    frontweight = w1 + w2;
    frontarm = plane.arms.front;
    frontmoment = frontweight * frontarm;

    $("#frontweight").html(frontweight.toFixed(0) + "kg");
    $("#frontarm").html(frontarm.toFixed(2) + "m");
    $("#frontmoment").html(frontmoment.toFixed(0) + "kg.m");

    update_totals();
  }

  function update_rear() {
    console.log("REAR PAX", plane.arms.rear);
    var w1 = parseInt($("#pax2").val());
    var w2 = parseInt($("#pax3").val());
    if (plane.arms.rear == 0) {
      $("#pax2").val(0);
      $("#pax3").val(0);
      w1 = 0;
      w2 = 0;
    }
    rearweight = w1 + w2;
    reararm = plane.arms.rear;
    rearmoment = rearweight * reararm;

    $("#rearweight").html(rearweight.toFixed(0) + "kg");
    $("#reararm").html(reararm.toFixed(2) + "m");
    $("#rearmoment").html(rearmoment.toFixed(0) + "kg.m");

    update_totals();
  }

  function update_baggage() {
    console.log("BAGGAGE", plane.arms.baggage);
    bagweight = parseInt($("#baggage").val());
    bagarm = plane.arms.baggage;
    bagmoment = bagweight * bagarm;

    $("#bagweight").html(bagweight.toFixed(0) + "kg");
    $("#bagarm").html(bagarm.toFixed(2) + "m");
    $("#bagmoment").html(bagmoment.toFixed(0) + "kg.m");

    update_totals();
  }

  function update_baggage2() {
    console.log("BAGGAGE2", plane.arms.baggage2);
    bagweight2 = parseInt($("#baggage2").val());
    if (plane.bagmax2 == 0) {
      $("#baggage2").val(0);
      bagweight2 = 0;
    }
    bagarm2 = plane.arms.baggage2;
    bagmoment2 = bagweight2 * bagarm2;

    $("#bagweight2").html(bagweight2.toFixed(0) + "kg");
    $("#bagarm2").html(bagarm2.toFixed(2) + "m");
    $("#bagmoment2").html(bagmoment2.toFixed(0) + "kg.m");

    update_totals();
  }

  function update_mainfuel() {
    console.log("IN UPDATE FUEL", plane.arms.fuel);
    var value = parseFloat($("#mainfuel").val());
    if (plane.maxmainfuel == 0) {
      $("#mainfuel").val(0);
      value = 0;
    }
    mainfuelweight = value * essence?.density;
    mainfuelarm = plane.arms.mainfuel;
    mainfuelmoment = mainfuelweight * mainfuelarm;

    $("#mainfuelmass").html(mainfuelweight.toFixed(0) + "kg");
    $("#mainfuelarm").html(mainfuelarm.toFixed(2) + "m");
    $("#mainfuelmoment").html(mainfuelmoment.toFixed(0) + "kg.m");

    update_totals();
  }

  function update_wingfuel() {
    var w1 = parseInt($("#leftwingfuel").val());
    var w2 = parseInt($("#rightwingfuel").val());
    if (plane.maxwingfuel == 0) {
      $("#leftwingfuel").val(0);
      $("#rightwingfuel").val(0);
      w1 = 0;
      w2 = 0;
    }
    wingfuelweight = (w1 + w2) * essence?.density;
    wingfuelarm = plane.arms.wingfuel;
    wingfuelmoment = wingfuelweight * wingfuelarm;

    $("#wingfuelweight").html(wingfuelweight.toFixed(0) + "kg");
    $("#wingfuelarm").html(wingfuelarm.toFixed(2) + "m");
    $("#wingfuelmoment").html(wingfuelmoment.toFixed(0) + "kg.m");

    update_totals();
  }

  function update_auxfuel() {
    var value = parseInt($("#auxfuel").val());
    console.log(
      "IN UPDATE_AUXFUEL",
      value,
      plane.maxauxfuel,
      value > plane.maxauxfuel
    );
    if (plane.maxauxfuel == 0) {
      $("#auxfuel").val(0);
      value = 0;
    }
    auxfuelweight = value * 0.72;
    auxfuelarm = plane.arms.auxfuel;
    auxfuelmoment = auxfuelweight * auxfuelarm;

    $("#auxfuelmass").html(auxfuelweight.toFixed(0) + "kg");
    $("#auxfuelarm").html(auxfuelarm.toFixed(2) + "m");
    $("#auxfuelmoment").html(auxfuelmoment.toFixed(0) + "kg.m");

    update_totals();
  }

  // Initialization of the form
  update_plane();
  update_front();
  update_rear();
  update_baggage();
  update_baggage2();
  update_mainfuel();
  update_wingfuel();
  update_auxfuel();

  // Event callbacks
  $("#callsign").on("change", update_plane);
  $("#pax0, #pax1").on("change", update_front);
  $("#pax2, #pax3").on("change", update_rear);
  $("#baggage").on("change", update_baggage);
  $("#baggage2").on("change", update_baggage2);
  $("#mainfuel").on("change", update_mainfuel);
  $("#leftwingfuel, #rightwingfuel").on("change", update_wingfuel);
  $("#auxfuel").on("change", update_auxfuel);
  $("#resetform").on("click", reset_form);
});
