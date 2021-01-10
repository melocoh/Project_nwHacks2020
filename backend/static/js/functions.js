
$(document).ready(function(){
    $('#loginbutton').click(function(){
        checklongin();
    });
});


var checklongin = function(){
    let setting = {
        'url':'http://127.0.0.1:5050/logincheck',
        "method": "GET",
        "crossDomain": true,
        "contentType" : "application/json"
    }
    $.ajax(setting).done(function(res){
        if (res.status == 'False'){
            console.log(res.status)
            window.open("http://127.0.0.1:5050/login", '_blank');
            
        }else{
            window.location.replace("C:\\Users\\Shreyas Kudari\\Documents\\semester5\\Project_nwHacks2020\\FrontEnd\\home.html")
        }
    });
}