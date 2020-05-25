

$(document).ready(function() {

    var name;
    var plane;
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

    $('#plane').on('change', function(){
        name = $('#plane').val();
        plane = planes[name];
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

        update_totals();
    });

    $('#pax0, #pax1').on('change', function(){
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
    });

    $('#pax2, #pax3').on('change', function(){
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
    });

    $('#baggage').on('change', function(){
        console.log(plane.arms.baggage);
        bagweight = parseInt($(this).val());
        bagarm = plane.arms.baggage;
        bagmoment = bagweight * bagarm;

        $("#bagweight").html(bagweight.toFixed(3));
        $('#bagarm').html(bagarm);
        $('#bagmoment').html(bagmoment.toFixed(3));

        update_totals();
    });

    $('#fuelgauge').on('change', function(){
        console.log(plane.arms.fuel);
        var gauge = parseFloat($(this).val());
        console.log(gauge, plane.maxfuel)
        fuelweight = gauge * plane.maxfuel / 4;
        fuelarm = plane.arms.fuel;
        fuelmoment = fuelweight * fuelarm;

        $("#fuelmass").html(fuelweight.toFixed(3));
        $('#fuelarm').html(fuelarm);
        $('#fuelmoment').html(fuelmoment.toFixed(3));

        update_totals();
    });


    $('#auxfuel').on('change', function(){
        auxfuel = parseFloat($(this).val());
        auxfuelweight = auxfuel * .72;
        auxfuelarm = plane.arms.auxfuel;
        auxfuelmoment = auxfuelweight * auxfuelarm;

        $("#auxfuelmass").html(auxfuelweight.toFixed(3));
        $('#auxfuelarm').html(auxfuelarm);
        $('#auxfuelmoment').html(auxfuelmoment.toFixed(3));

        update_totals();
    });

    
});