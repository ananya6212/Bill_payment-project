let cart = [];


/* -------------------------------------------------------
   Add Product To Cart
------------------------------------------------------- */

function addToCart() {

    const productSelect =
        document.getElementById("product_name");

    const quantityInput =
        document.getElementById("quantity");

    const message =
        document.getElementById("stock-message");


    if (!productSelect || !quantityInput) {
        console.error("Product or quantity element not found.");
        return;
    }


    const selectedOption =
        productSelect.options[
            productSelect.selectedIndex
        ];


    if (!selectedOption || !selectedOption.value) {

        if (message) {
            message.textContent =
                "Please select a product.";

            message.className =
                "stock-message error";
        }

        return;
    }


    const productName =
        selectedOption.value;


    const price =
        parseFloat(
            selectedOption.dataset.price
        );


    const stock =
        parseInt(
            selectedOption.dataset.stock,
            10
        );


    const quantity =
        parseInt(
            quantityInput.value,
            10
        );


    if (!quantity || quantity <= 0) {

        if (message) {
            message.textContent =
                "Enter a valid quantity.";

            message.className =
                "stock-message error";
        }

        return;
    }


    if (quantity > stock) {

        if (message) {
            message.textContent =
                `Only ${stock} unit(s) available.`;

            message.className =
                "stock-message error";
        }

        return;
    }


    /* ---------------------------------------------------
       Check if product already exists in cart
    --------------------------------------------------- */

    const existing =
        cart.find(
            item =>
                item.name === productName
        );


    if (existing) {

        const newQuantity =
            existing.quantity + quantity;


        if (newQuantity > stock) {

            if (message) {
                message.textContent =
                    `Only ${stock} unit(s) available.`;

                message.className =
                    "stock-message error";
            }

            return;
        }


        existing.quantity =
            newQuantity;


        existing.amount =
            existing.quantity *
            existing.price;

    } else {

        cart.push({

            name: productName,

            price: price,

            quantity: quantity,

            stock: stock,

            amount:
                price * quantity

        });

    }


    /* ---------------------------------------------------
       Success message
    --------------------------------------------------- */

    if (message) {

        message.textContent =
            `${productName} added to cart.`;

        message.className =
            "stock-message success";
    }


    renderCart();


    /* Reset product and quantity */

    productSelect.value = "";

    quantityInput.value = 1;

}


/* -------------------------------------------------------
   Render Cart
------------------------------------------------------- */

function renderCart() {

    const cartBody =
        document.getElementById("cart-body");


    if (!cartBody) {
        console.error("Cart body not found.");
        return;
    }


    cartBody.innerHTML = "";


    /* ---------------------------------------------------
       Empty cart
    --------------------------------------------------- */

    if (cart.length === 0) {

        cartBody.innerHTML = `

            <tr>

                <td
                    colspan="5"
                    class="empty-row"
                >
                    No products added yet.
                </td>

            </tr>

        `;

        updateHiddenFields();

        calculateTotals();

        return;
    }


    /* ---------------------------------------------------
       Products
    --------------------------------------------------- */

    cart.forEach(
        (item, index) => {

            const row =
                document.createElement("tr");


            row.innerHTML = `

                <td>
                    ${escapeHtml(item.name)}
                </td>

                <td>
                    ₹${item.price.toFixed(2)}
                </td>

                <td>
                    ${item.quantity}
                </td>

                <td>
                    ₹${item.amount.toFixed(2)}
                </td>

                <td>

                    <button
                        type="button"
                        class="btn-delete"
                        onclick="removeFromCart(${index})"
                    >
                        Remove
                    </button>

                </td>

            `;


            cartBody.appendChild(row);

        }
    );


    updateHiddenFields();

    calculateTotals();

}


/* -------------------------------------------------------
   Remove Product
------------------------------------------------------- */

function removeFromCart(index) {

    if (
        index < 0 ||
        index >= cart.length
    ) {
        return;
    }


    cart.splice(
        index,
        1
    );


    renderCart();

}


/* -------------------------------------------------------
   Clear Cart
------------------------------------------------------- */

function clearCart() {

    if (cart.length === 0) {
        return;
    }


    const confirmed =
        confirm(
            "Clear all products from the cart?"
        );


    if (!confirmed) {
        return;
    }


    cart = [];


    renderCart();


    const message =
        document.getElementById(
            "stock-message"
        );


    if (message) {

        message.textContent =
            "";

        message.className =
            "stock-message";
    }

}


/* -------------------------------------------------------
   Calculate Totals
------------------------------------------------------- */

function calculateTotals() {

    let subtotal = 0;


    cart.forEach(
        item => {

            subtotal +=
                item.amount;

        }
    );


    const discountInput =
        document.getElementById(
            "discount_percent"
        );


    const taxInput =
        document.getElementById(
            "tax_percent"
        );


    let discountPercent =
        discountInput
            ? parseFloat(
                discountInput.value
            ) || 0
            : 0;


    let taxPercent =
        taxInput
            ? parseFloat(
                taxInput.value
            ) || 0
            : 0;


    /* Keep percentages between 0 and 100 */

    discountPercent =
        Math.min(
            100,
            Math.max(
                0,
                discountPercent
            )
        );


    taxPercent =
        Math.min(
            100,
            Math.max(
                0,
                taxPercent
            )
        );


    const discountAmount =
        subtotal *
        discountPercent /
        100;


    const taxableAmount =
        Math.max(
            0,
            subtotal -
            discountAmount
        );


    const taxAmount =
        taxableAmount *
        taxPercent /
        100;


    const grandTotal =
        taxableAmount +
        taxAmount;


    /* ---------------------------------------------------
       Main totals
    --------------------------------------------------- */

    setText(
        "subtotal",
        formatCurrency(subtotal)
    );


    setText(
        "discountAmount",
        "- " +
        formatCurrency(discountAmount)
    );


    setText(
        "taxAmount",
        "+ " +
        formatCurrency(taxAmount)
    );


    setText(
        "grandTotal",
        formatCurrency(grandTotal)
    );


    /* ---------------------------------------------------
       Invoice Preview
    --------------------------------------------------- */

    setText(
        "preview-items",
        cart.length
    );


    setText(
        "preview-subtotal",
        formatCurrency(subtotal)
    );


    setText(
        "preview-discount",
        "- " +
        formatCurrency(discountAmount)
    );


    setText(
        "preview-tax",
        "+ " +
        formatCurrency(taxAmount)
    );


    setText(
        "preview-total",
        formatCurrency(grandTotal)
    );

}


/* -------------------------------------------------------
   Update Hidden Fields
------------------------------------------------------- */

function updateHiddenFields() {

    const hiddenContainer =
        document.getElementById(
            "hidden-cart-fields"
        );


    if (!hiddenContainer) {
        return;
    }


    hiddenContainer.innerHTML = "";


    if (cart.length === 0) {
        return;
    }


    /* Product names */

    const productNames =
        document.createElement("input");

    productNames.type =
        "hidden";

    productNames.id =
        "productNames";

    productNames.name =
        "product_names";

    productNames.value =
        cart
            .map(
                item => item.name
            )
            .join(",");


    /* Quantities */

    const quantities =
        document.createElement("input");

    quantities.type =
        "hidden";

    quantities.id =
        "quantities";

    quantities.name =
        "quantities";

    quantities.value =
        cart
            .map(
                item => item.quantity
            )
            .join(",");


    hiddenContainer.appendChild(
        productNames
    );


    hiddenContainer.appendChild(
        quantities
    );

}


/* -------------------------------------------------------
   Validate Invoice
------------------------------------------------------- */

function validateInvoice() {

    const customer =
        document.getElementById(
            "customer_name"
        );


    if (
        !customer ||
        !customer.value.trim()
    ) {

        alert(
            "Please enter customer name."
        );

        return false;
    }


    if (cart.length === 0) {

        alert(
            "Please add at least one product."
        );

        return false;
    }


    updateHiddenFields();


    return true;

}


/* -------------------------------------------------------
   Helpers
------------------------------------------------------- */

function getTotalUnits() {

    return cart.reduce(
        (
            total,
            item
        ) =>
            total +
            item.quantity,
        0
    );

}


function formatCurrency(value) {

    return "₹" +
        Number(value).toFixed(2);

}


function setText(
    id,
    value
) {

    const element =
        document.getElementById(id);


    if (element) {

        element.textContent =
            value;

    }

}


function escapeHtml(value) {

    return String(value)
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );

}


/* -------------------------------------------------------
   Initialisation
------------------------------------------------------- */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        /* -----------------------------------------------
           Initial cart render
        ----------------------------------------------- */

        renderCart();


        /* -----------------------------------------------
           ADD BUTTON
        ----------------------------------------------- */

        const addButton =
            document.getElementById(
                "add-product"
            );


        if (addButton) {

            addButton.addEventListener(
                "click",
                addToCart
            );

        }


        /* -----------------------------------------------
           CLEAR CART BUTTON
        ----------------------------------------------- */

        const clearButton =
            document.getElementById(
                "clear-cart"
            );


        if (clearButton) {

            clearButton.addEventListener(
                "click",
                clearCart
            );

        }


        /* -----------------------------------------------
           Discount and Tax
        ----------------------------------------------- */

        const discountInput =
            document.getElementById(
                "discount_percent"
            );


        const taxInput =
            document.getElementById(
                "tax_percent"
            );


        if (discountInput) {

            discountInput.addEventListener(
                "input",
                calculateTotals
            );

        }


        if (taxInput) {

            taxInput.addEventListener(
                "input",
                calculateTotals
            );

        }


        /* -----------------------------------------------
           Invoice Form Submit
        ----------------------------------------------- */

        const invoiceForm =
            document.querySelector(
                'form[action="/invoices/create"]'
            );


        if (invoiceForm) {

            invoiceForm.addEventListener(
                "submit",
                function (event) {

                    if (!validateInvoice()) {

                        event.preventDefault();

                    }

                }
            );

        }

    }
);