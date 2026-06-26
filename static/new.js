let quantity = 1;
let selectedProductId = null;
function openProduct(card){
     selectedProductId = card.dataset.id;
    document.getElementById("modalImage").src =
        card.dataset.image;

    document.getElementById("modalName").innerHTML =
        card.dataset.name;

    document.getElementById("modalCategory").innerHTML =
        card.dataset.category;

    document.getElementById("modalExpiry").innerHTML =
        card.dataset.expiry;

    document.getElementById("modalPrice").innerHTML =
        "₹"+card.dataset.price;

    document.getElementById("modalOriginal").innerHTML =
        "₹"+card.dataset.original;

    document.getElementById("modalQuantity").innerHTML =
    card.dataset.quantity + " left";

    document.getElementById("modalDiscount").innerHTML =
        card.dataset.discount + "% OFF";

    // Reset quantity whenever a new product is opened
    quantity = 1;
    document.getElementById("quantityValue").innerHTML = quantity;

    // Show popup
    document.getElementById("productModal").style.display = "flex";

}

function closeProduct(){

    document.getElementById("productModal").style.display="none";

}

window.onclick=function(e){

    if(e.target==document.getElementById("productModal")){

        closeProduct();

    }

}
function increaseQty() {
    quantity++;
    document.getElementById("quantityValue").innerHTML = quantity;
}

function decreaseQty() {
    if (quantity > 1) {
        quantity--;
        document.getElementById("quantityValue").innerHTML = quantity;
    }
}

function addToCart(){

    fetch("/add_to_cart",{

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({

            product_id:selectedProductId,

            quantity:quantity

        })

    })

    .then(response=>response.json())

    .then(data => {

    updateCartCount();

    closeProduct();

});

}
function updateCartCount(){

    fetch("/cart_count")

    .then(res=>res.json())

    .then(data=>{

        document.getElementById("cartCount").innerHTML=data.count;

    });

}
window.onload=function(){

    updateCartCount();

}
function openCart(){

    document.getElementById("cartPanel").classList.add("show");

    fetch("/cart")
    .then(res => res.json())
    .then(items => {

        let html = "";
        let total = 0;

        if(items.length === 0){

            html = "<p style='padding:20px'>Your cart is empty.</p>";

        }else{

            items.forEach(item => {
                total += item.discount_price * item.quantity;
                html += `
<div class="cart-item">

    <img src="/static/images/${item.image}" class="cart-img">

    <div class="cart-details">

        <h4>${item.name}</h4>

        <p class="store-name">FreshSave Market</p>

        <div class="qty-box">

            <button onclick="decreaseCart(${item.id})">−</button>

            <span>${item.quantity}</span>

            <button onclick="increaseCart(${item.id})">+</button>

        </div>

    </div>

    <div class="price-box">

        <span class="cart-price">
            ₹${item.discount_price}
        </span>

        <i class="fa-regular fa-trash-can"
           onclick="deleteCart(${item.id})"></i>

    </div>

</div>
`;

            });

        }

        document.getElementById("cartItems").innerHTML = html;
        document.getElementById("cartTotal").innerHTML =
    "₹" + total.toFixed(2);

    });

}

function closeCart(){

    document.getElementById("cartPanel").classList.remove("show");

}
function increaseCart(id){

    fetch("/increase_cart",{

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({

            product_id:id

        })

    })

    .then(()=>{

        updateCartCount();

        openCart();

    });

}

function deleteCart(id){

    fetch("/delete_cart",{

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({

            product_id:id

        })

    })

    .then(()=>{

        updateCartCount();

        openCart();

    });

}
function placeOrder(){

    fetch("/create_order",{
        method:"POST"
    })
    .then(res => res.json())
    .then(data => {

        if(!data.success){
            alert(data.error);
            return;
        }

        var options = {

            key: data.key,

            amount: data.amount,

            currency: "INR",

            name: "FreshSave",

            description: "Food Order",

            order_id: data.order_id,

           handler: function (response) {

    console.log(response);

    fetch("/place_order", {
        method: "POST"
    })
    .then(res => res.json())
    .then(data => {

        if (data.success) {

            alert("Payment Successful!");

            closeCart();

            updateCartCount();

            location.reload();

        } else {

            alert(data.message);

        }

    });

},

            theme: {
                color: "#176b36"
            }

        };

        var rzp = new Razorpay(options);

        rzp.open();

    });

}