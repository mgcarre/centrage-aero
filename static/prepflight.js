
$(document).ready(function() {

    var callsign;
    var bew = 0;
    var frontweight = 0;
    var rearweight = 0;
    var bagweight = 0;
    var fuelweight = 0;
    var auxfuelweight = 0;
    var auw;
    var bemoment = 0;
    var frontmoment = 0;
    var rearmoment = 0;
    var bagmoment = 0;
    var fuelmoment = 0;
    var auxfuelmoment =0;
    var moment;
    var cg;

    function update_totals() {
        auw = [bew, frontweight, rearweight, 
                bagweight, fuelweight, auxfuelweight].reduce((a, b)=> a +b);
        console.log('TOTALS', fuelweight, auw)
        moment = [bemoment, frontmoment, rearmoment,
                bagmoment, fuelmoment, auxfuelmoment].reduce((a, b)=> a + b);
        cg = moment / auw;

        $('#auw').html(auw.toFixed(3));
        $('#cg').html(cg.toFixed(3));
        $('#moment').html(moment.toFixed(3));
    };

    function update_plane(){
        callsign = $('#callsign').val();
        plane = planes[callsign];
        console.log("PLANE", plane)

        // update the plane's max aux fuel size
        var selectbox = $('#auxfuel');
        var list = '';
        for (i = 0; i <= plane.maxauxfuel; i += 5){
            list += "<option value='" + i + "'>" + i + "</option>";
        }
        selectbox.empty().append(list);

        planetype = plane.planetype;
        bew = plane.bew;
        bearm = plane.arms.bew;
        bemoment = (bew * bearm);

        $('#planetype').html(planetype);
        $('#bew').html(bew.toFixed(3));
        $('#bearm').html(bearm);
        $('#bemoment').html(bemoment.toFixed(3));

        update_front();
        update_rear();
        update_fuel();
        update_auxfuel();
        update_totals();
    }

    function update_front() {
        console.log("PAX", plane);//.arms.front);
        var w1 = parseInt($('#pax0').val());
        var w2 = parseInt($('#pax1').val());
        frontweight = w1 + w2;
        frontarm = plane.arms.front;
        frontmoment = frontweight * frontarm;

        $("#frontweight").html(frontweight.toFixed(3));
        $('#frontarm').html(frontarm);
        $('#frontmoment').html(frontmoment.toFixed(3));

        update_totals();
    }

    function update_rear() {
        console.log(plane.arms.rear);
        var w1 = parseInt($('#pax2').val());
        var w2 = parseInt($('#pax3').val());
        rearweight = w1 + w2;
        reararm = plane.arms.rear;
        rearmoment = rearweight * reararm;

        $("#rearweight").html(rearweight.toFixed(3));
        $('#reararm').html(reararm);
        $('#rearmoment').html(rearmoment.toFixed(3));

        update_totals();
    }

    function update_baggage() {
        console.log(plane.arms.baggage);
        bagweight = parseInt($('#baggage').val());
        bagarm = plane.arms.baggage;
        bagmoment = bagweight * bagarm;

        $("#bagweight").html(bagweight.toFixed(3));
        $('#bagarm').html(bagarm);
        $('#bagmoment').html(bagmoment.toFixed(3));

        update_totals();
    }

    function update_fuel() {
        console.log(plane.arms.fuel);
        var gauge = parseFloat($('#fuelgauge').val());
        console.log(gauge, plane.maxfuel)
        fuelweight = gauge * plane.maxfuel / 4 * .72;
        fuelarm = plane.arms.fuel;
        fuelmoment = fuelweight * fuelarm;

        $("#fuelmass").html(fuelweight.toFixed(3));
        $('#fuelarm').html(fuelarm);
        $('#fuelmoment').html(fuelmoment.toFixed(3));

        update_totals();
    }

    function update_auxfuel() {
        auxfuel = parseFloat($('#auxfuel').val());
        auxfuelweight = auxfuel * .72;
        auxfuelarm = plane.arms.auxfuel;
        auxfuelmoment = auxfuelweight * auxfuelarm;

        $("#auxfuelmass").html(auxfuelweight.toFixed(3));
        $('#auxfuelarm').html(auxfuelarm);
        $('#auxfuelmoment').html(auxfuelmoment.toFixed(3));

        update_totals();
    }

    // Initialization of the form
    update_plane();
    update_front();
    update_rear();
    update_baggage();
    update_fuel();
    update_auxfuel();

    // Event callbacks
    $('#callsign').on('change', update_plane);
    $('#pax0, #pax1').on('change', update_front);
    $('#pax2, #pax3').on('change', update_rear);
    $('#baggage').on('change', update_baggage);
    $('#fuelgauge').on('change', update_fuel);
    $('#auxfuel').on('change', update_auxfuel);
    
});