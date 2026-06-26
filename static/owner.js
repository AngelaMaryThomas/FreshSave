function deleteProduct(id){

    if(!confirm("Delete this product?")){
        return;
    }

    fetch("/delete_product",{

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({

            product_id:id

        })

    })

    .then(res=>res.json())

    .then(data=>{

        alert(data.message);

        if(data.success){

            location.reload();

        }

    });

}