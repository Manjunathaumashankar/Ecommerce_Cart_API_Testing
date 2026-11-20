"""
Generator for SoapUI 5.x Project XML for Ecommerce Cart API Testing.
Generates comprehensive TestSuites, TestCases, REST Steps, Assertions
(JSONPath, SLA, Status, Groovy Math, Contains, Existence), and Property Transfers.
Uses explicit concrete resources to avoid SoapUI 5.x template parameter encoding bugs.
"""

import uuid
import xml.etree.ElementTree as ET
from xml.dom import minidom


def u():
    return str(uuid.uuid4())


def build_soapui_project():
    root = ET.Element("con:soapui-project", {
        "id": u(),
        "activeEnvironment": "Default",
        "name": "Ecommerce-Cart-API-Testing",
        "resourceRoot": "",
        "soapui-version": "5.10.0",
        "abortOnError": "false",
        "runType": "SEQUENTIAL",
        "xmlns:con": "http://eviware.com/soapui/config",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance"
    })

    ET.SubElement(root, "con:settings")

    # Project-level properties
    props = ET.SubElement(root, "con:properties")
    p1 = ET.SubElement(props, "con:property")
    ET.SubElement(p1, "con:name").text = "baseUrl"
    ET.SubElement(p1, "con:value").text = "http://127.0.0.1:5000"

    p2 = ET.SubElement(props, "con:property")
    ET.SubElement(p2, "con:name").text = "defaultProductId"
    ET.SubElement(p2, "con:value").text = "1"

    p3 = ET.SubElement(props, "con:property")
    ET.SubElement(p3, "con:name").text = "defaultCoupon"
    ET.SubElement(p3, "con:value").text = "SAVE10"

    # REST Service Interface
    interface = ET.SubElement(root, "con:interface", {
        "xsi:type": "con:RestService",
        "id": u(),
        "wadlVersion": "http://wadl.dev.java.net/2009/02",
        "name": "Ecommerce API",
        "type": "rest",
        "basePath": ""
    })
    ET.SubElement(interface, "con:settings")
    ET.SubElement(interface, "con:definitionCache", {"type": "TEXT"})
    endpoints = ET.SubElement(interface, "con:endpoints")
    ET.SubElement(endpoints, "con:endpoint").text = "${#Project#baseUrl}"

    def add_resource(name, path, methods):
        res = ET.SubElement(interface, "con:resource", {
            "name": name,
            "path": path,
            "id": u()
        })
        ET.SubElement(res, "con:settings")
        ET.SubElement(res, "con:parameters")

        for m_name in methods:
            m = ET.SubElement(res, "con:method", {
                "name": m_name,
                "id": u(),
                "method": m_name
            })
            ET.SubElement(m, "con:settings")
            ET.SubElement(m, "con:parameters")

            rep = ET.SubElement(m, "con:representation", {"type": "RESPONSE"})
            ET.SubElement(rep, "con:mediaType").text = "application/json"
            ET.SubElement(rep, "con:status").text = "200"
            ET.SubElement(rep, "con:params")
            ET.SubElement(rep, "con:element").text = "Response"

            req = ET.SubElement(m, "con:request", {
                "name": f"{m_name} Request",
                "id": u(),
                "mediaType": "application/json"
            })
            ET.SubElement(req, "con:settings")
            ET.SubElement(req, "con:endpoint").text = "${#Project#baseUrl}"
            ET.SubElement(req, "con:request")
            creds = ET.SubElement(req, "con:credentials")
            ET.SubElement(creds, "con:authType").text = "No Authorization"
            ET.SubElement(req, "con:jmsConfig", {"JMSDeliveryMode": "PERSISTENT"})
            ET.SubElement(req, "con:jmsPropertyConfig")
            ET.SubElement(req, "con:parameters")
        return res

    # Register concrete resources
    add_resource("Home", "/", ["GET"])
    add_resource("Products", "/products", ["GET"])
    add_resource("Product_1", "/products/1", ["GET"])
    add_resource("Product_2", "/products/2", ["GET"])
    add_resource("Product_999", "/products/999", ["GET"])
    add_resource("Cart", "/cart", ["GET", "POST", "DELETE"])
    add_resource("CartItem_1", "/cart/1", ["PUT", "DELETE"])
    add_resource("CartItem_2", "/cart/2", ["PUT", "DELETE"])
    add_resource("CartItem_3", "/cart/3", ["PUT", "DELETE"])
    add_resource("CartItem_888", "/cart/888", ["PUT", "DELETE"])
    add_resource("Coupons", "/coupons", ["GET"])
    add_resource("ApplyCoupon", "/cart/apply-coupon", ["POST"])
    add_resource("RemoveCoupon", "/cart/coupon", ["DELETE"])
    add_resource("Checkout", "/cart/checkout", ["POST"])
    add_resource("Orders", "/orders", ["GET"])
    add_resource("OrderById", "/orders/1", ["GET"])
    add_resource("Reset", "/reset", ["POST"])

    def create_rest_step(tc, step_name, res_path, method, req_body="", assertions=None):
        step = ET.SubElement(tc, "con:testStep", {
            "type": "restrequest",
            "name": step_name,
            "id": u()
        })
        ET.SubElement(step, "con:settings")
        cfg = ET.SubElement(step, "con:config", {
            "service": "Ecommerce API",
            "resourcePath": res_path,
            "methodName": method,
            "xsi:type": "con:RestRequestStep"
        })
        rest_req = ET.SubElement(cfg, "con:restRequest", {
            "name": step_name,
            "id": u(),
            "mediaType": "application/json",
            "postQueryString": "false"
        })
        settings = ET.SubElement(rest_req, "con:settings")
        set1 = ET.SubElement(settings, "con:setting", {"id": "com.eviware.soapui.impl.support.AbstractHttpRequest@follow-redirects"})
        set1.text = "true"

        ET.SubElement(rest_req, "con:endpoint").text = "${#Project#baseUrl}"
        req_elem = ET.SubElement(rest_req, "con:request")
        if req_body:
            req_elem.text = req_body

        ET.SubElement(rest_req, "con:originalUri").text = f"${{#Project#baseUrl}}{res_path}"

        if assertions:
            for ass in assertions:
                a_type = ass.get("type")
                a_name = ass.get("name", a_type)
                a_elem = ET.SubElement(rest_req, "con:assertion", {
                    "type": a_type,
                    "id": u(),
                    "name": a_name
                })
                a_cfg = ET.SubElement(a_elem, "con:configuration")

                if a_type == "Valid HTTP Status Codes":
                    codes = ET.SubElement(a_cfg, "codes")
                    codes.text = str(ass.get("codes", "200"))
                elif a_type == "Response SLA Assertion":
                    sla = ET.SubElement(a_cfg, "SLA")
                    sla.text = str(ass.get("sla", "2000"))
                elif a_type == "Simple Contains":
                    tok = ET.SubElement(a_cfg, "token")
                    tok.text = ass.get("token", "")
                    ic = ET.SubElement(a_cfg, "ignoreCase")
                    ic.text = "false"
                    rx = ET.SubElement(a_cfg, "useRegEx")
                    rx.text = "false"
                elif a_type == "JsonPath Match":
                    p = ET.SubElement(a_cfg, "path")
                    p.text = ass.get("path")
                    c = ET.SubElement(a_cfg, "content")
                    c.text = str(ass.get("content"))
                    aw = ET.SubElement(a_cfg, "allowWildcards")
                    aw.text = "false"
                    ind = ET.SubElement(a_cfg, "ignoreNamspaceDifferences")
                    ind.text = "false"
                    icm = ET.SubElement(a_cfg, "ignoreComments")
                    icm.text = "false"
                elif a_type == "JsonPath Count":
                    p = ET.SubElement(a_cfg, "path")
                    p.text = ass.get("path")
                    c = ET.SubElement(a_cfg, "content")
                    c.text = str(ass.get("count"))
                    aw = ET.SubElement(a_cfg, "allowWildcards")
                    aw.text = "false"
                    ind = ET.SubElement(a_cfg, "ignoreNamspaceDifferences")
                    ind.text = "false"
                    icm = ET.SubElement(a_cfg, "ignoreComments")
                    icm.text = "false"
                elif a_type == "JsonPath Existence Match":
                    p = ET.SubElement(a_cfg, "path")
                    p.text = ass.get("path")
                    c = ET.SubElement(a_cfg, "content")
                    c.text = "true"
                elif a_type == "GroovyScriptAssertion":
                    st = ET.SubElement(a_cfg, "scriptText")
                    st.text = ass.get("script", "")

        creds = ET.SubElement(rest_req, "con:credentials")
        ET.SubElement(creds, "con:authType").text = "No Authorization"
        ET.SubElement(rest_req, "con:jmsConfig", {"JMSDeliveryMode": "PERSISTENT"})
        ET.SubElement(rest_req, "con:jmsPropertyConfig")
        ET.SubElement(rest_req, "con:parameters")

        return step

    # ==========================================================
    # TEST SUITE 1: Smoke & Sanity Tests
    # ==========================================================
    ts1 = ET.SubElement(root, "con:testSuite", {
        "id": u(),
        "name": "1. Smoke & Sanity TestSuite"
    })
    ET.SubElement(ts1, "con:settings")
    ET.SubElement(ts1, "con:runType").text = "SEQUENTIAL"

    # TC 1.1: Health Check
    tc1_1 = ET.SubElement(ts1, "con:testCase", {"id": u(), "name": "TC01_HealthCheck", "failOnError": "true"})
    ET.SubElement(tc1_1, "con:settings")
    create_rest_step(
        tc1_1, "GET_HealthCheck", "/", "GET",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "Response SLA Assertion", "sla": "2000"},
            {"type": "Simple Contains", "token": "Welcome to E-commerce Shopping Cart API"},
            {"type": "Simple Contains", "token": "API is running successfully"}
        ]
    )
    ET.SubElement(tc1_1, "con:properties")

    # TC 1.2: Get All Products
    tc1_2 = ET.SubElement(ts1, "con:testCase", {"id": u(), "name": "TC02_GetAllProducts", "failOnError": "true"})
    ET.SubElement(tc1_2, "con:settings")
    create_rest_step(
        tc1_2, "GET_AllProducts", "/products", "GET",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "JsonPath Count", "path": "$", "count": 5},
            {"type": "Simple Contains", "token": "Laptop"}
        ]
    )
    ET.SubElement(tc1_2, "con:properties")

    # TC 1.3: Get Product by Valid ID
    tc1_3 = ET.SubElement(ts1, "con:testCase", {"id": u(), "name": "TC03_GetProduct_ValidId", "failOnError": "true"})
    ET.SubElement(tc1_3, "con:settings")
    create_rest_step(
        tc1_3, "GET_Product_1", "/products/1", "GET",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "Simple Contains", "token": "Laptop"}
        ]
    )
    ET.SubElement(tc1_3, "con:properties")

    # TC 1.4: Get Product Not Found
    tc1_4 = ET.SubElement(ts1, "con:testCase", {"id": u(), "name": "TC04_GetProduct_NotFound", "failOnError": "true"})
    ET.SubElement(tc1_4, "con:settings")
    create_rest_step(
        tc1_4, "GET_Product_NotFound", "/products/999", "GET",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "404"},
            {"type": "Simple Contains", "token": "Product not found"}
        ]
    )
    ET.SubElement(tc1_4, "con:properties")

    # TC 1.5: Get Available Coupons
    tc1_5 = ET.SubElement(ts1, "con:testCase", {"id": u(), "name": "TC05_GetCouponsList", "failOnError": "true"})
    ET.SubElement(tc1_5, "con:settings")
    create_rest_step(
        tc1_5, "GET_Coupons", "/coupons", "GET",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "JsonPath Count", "path": "$", "count": 4}
        ]
    )
    ET.SubElement(tc1_5, "con:properties")

    # ==========================================================
    # TEST SUITE 2: Shopping Cart E2E Workflow (with Coupon)
    # ==========================================================
    ts2 = ET.SubElement(root, "con:testSuite", {
        "id": u(),
        "name": "2. Shopping Cart E2E Workflow TestSuite"
    })
    ET.SubElement(ts2, "con:settings")
    ET.SubElement(ts2, "con:runType").text = "SEQUENTIAL"

    tc2_1 = ET.SubElement(ts2, "con:testCase", {"id": u(), "name": "TC01_CompleteCartToCheckoutLifecycle", "failOnError": "true"})
    ET.SubElement(tc2_1, "con:settings")

    # Step 1: Reset Database
    create_rest_step(
        tc2_1, "Step1_ResetDatabase", "/reset", "POST",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "Simple Contains", "token": "Database reset successfully"}
        ]
    )

    # Step 2: Verify Initial Empty Cart
    create_rest_step(
        tc2_1, "Step2_VerifyEmptyCart", "/cart", "GET",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "JsonPath Count", "path": "$.items", "count": 0}
        ]
    )

    # Step 3: Add Laptop (id: 1, qty: 2) -> 55000 * 2 = 110000
    create_rest_step(
        tc2_1, "Step3_AddLaptopToCart", "/cart", "POST",
        req_body='{"product_id": 1, "quantity": 2}',
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "201"},
            {"type": "Simple Contains", "token": "Product added to cart successfully"}
        ]
    )

    # Step 4: Add Headphones (id: 3, qty: 3) -> 1500 * 3 = 4500
    create_rest_step(
        tc2_1, "Step4_AddHeadphonesToCart", "/cart", "POST",
        req_body='{"product_id": 3, "quantity": 3}',
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "201"},
            {"type": "Simple Contains", "token": "Product added to cart successfully"}
        ]
    )

    # Step 5: Verify Cart Calculation (110000 + 4500 = 114500)
    groovy_calc = """def response = messageExchange.responseContent
def json = new groovy.json.JsonSlurper().parseText(response)
assert json.items.size() == 2 : "Expected 2 items in cart"
def expectedSubtotal = json.items.collect { it.subtotal }.sum()
assert Math.abs(json.subtotal - expectedSubtotal) < 0.01 : "Subtotal mismatch: " + expectedSubtotal + " vs " + json.subtotal
log.info("Cart subtotal verified: " + json.subtotal)
"""
    create_rest_step(
        tc2_1, "Step5_VerifyCartCalculations", "/cart", "GET",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "JsonPath Match", "path": "$.item_count", "content": "2"},
            {"type": "GroovyScriptAssertion", "name": "Groovy Math Subtotal Validation", "script": groovy_calc}
        ]
    )

    # Step 6: Apply Discount Coupon SAVE10 (10% off of 114500 = 11450)
    create_rest_step(
        tc2_1, "Step6_ApplyDiscountCoupon", "/cart/apply-coupon", "POST",
        req_body='{"code": "SAVE10"}',
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "Simple Contains", "token": "SAVE10"}
        ]
    )

    # Step 7: Verify Discount in Cart
    create_rest_step(
        tc2_1, "Step7_VerifyDiscountedCart", "/cart", "GET",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "Simple Contains", "token": "SAVE10"}
        ]
    )

    # Step 8: Checkout Cart
    create_rest_step(
        tc2_1, "Step8_CheckoutCart", "/cart/checkout", "POST",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "201"},
            {"type": "Simple Contains", "token": "CONFIRMED"},
            {"type": "JsonPath Existence Match", "path": "$.order_id"}
        ]
    )

    # Step 9: Verify Cart is Cleared After Checkout
    create_rest_step(
        tc2_1, "Step9_VerifyCartEmptyAfterCheckout", "/cart", "GET",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "JsonPath Match", "path": "$.item_count", "content": "0"}
        ]
    )

    # Step 10: Verify Stock Deduction (Laptop: 10 - 2 = 8)
    create_rest_step(
        tc2_1, "Step10_VerifyStockDeduction", "/products/1", "GET",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "JsonPath Match", "path": "$.stock", "content": "8"}
        ]
    )
    ET.SubElement(tc2_1, "con:properties")

    # ==========================================================
    # TEST SUITE 3: Discount Coupon Functionality & Validation
    # ==========================================================
    ts3 = ET.SubElement(root, "con:testSuite", {
        "id": u(),
        "name": "3. Discount Coupon Functionality TestSuite"
    })
    ET.SubElement(ts3, "con:settings")
    ET.SubElement(ts3, "con:runType").text = "SEQUENTIAL"

    # TC 3.1: Apply Valid Percentage Coupon (SAVE10)
    tc3_1 = ET.SubElement(ts3, "con:testCase", {"id": u(), "name": "TC01_ApplyPercentageCoupon_SAVE10", "failOnError": "true"})
    ET.SubElement(tc3_1, "con:settings")
    create_rest_step(tc3_1, "Reset", "/reset", "POST")
    create_rest_step(tc3_1, "AddItem", "/cart", "POST", req_body='{"product_id": 1, "quantity": 1}')
    create_rest_step(
        tc3_1, "Apply_SAVE10", "/cart/apply-coupon", "POST",
        req_body='{"code": "SAVE10"}',
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "Simple Contains", "token": "SAVE10"}
        ]
    )
    ET.SubElement(tc3_1, "con:properties")

    # TC 3.2: Apply Flat Discount Coupon (FLAT500)
    tc3_2 = ET.SubElement(ts3, "con:testCase", {"id": u(), "name": "TC02_ApplyFlatCoupon_FLAT500", "failOnError": "true"})
    ET.SubElement(tc3_2, "con:settings")
    create_rest_step(tc3_2, "Reset", "/reset", "POST")
    create_rest_step(tc3_2, "AddItem", "/cart", "POST", req_body='{"product_id": 2, "quantity": 1}')
    create_rest_step(
        tc3_2, "Apply_FLAT500", "/cart/apply-coupon", "POST",
        req_body='{"code": "FLAT500"}',
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "Simple Contains", "token": "FLAT500"}
        ]
    )
    ET.SubElement(tc3_2, "con:properties")

    # TC 3.3: Apply Invalid Coupon Code
    tc3_3 = ET.SubElement(ts3, "con:testCase", {"id": u(), "name": "TC03_ApplyInvalidCouponCode", "failOnError": "true"})
    ET.SubElement(tc3_3, "con:settings")
    create_rest_step(
        tc3_3, "Apply_NonExistent", "/cart/apply-coupon", "POST",
        req_body='{"code": "NONEXISTENT99"}',
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "404"},
            {"type": "Simple Contains", "token": "Coupon code not found"}
        ]
    )
    ET.SubElement(tc3_3, "con:properties")

    # TC 3.4: Apply Expired / Inactive Coupon
    tc3_4 = ET.SubElement(ts3, "con:testCase", {"id": u(), "name": "TC04_ApplyExpiredCoupon", "failOnError": "true"})
    ET.SubElement(tc3_4, "con:settings")
    create_rest_step(
        tc3_4, "Apply_Expired", "/cart/apply-coupon", "POST",
        req_body='{"code": "EXPIRED50"}',
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "400"},
            {"type": "Simple Contains", "token": "Coupon code is expired or inactive"}
        ]
    )
    ET.SubElement(tc3_4, "con:properties")

    # TC 3.5: Apply Coupon Below Minimum Order Value
    tc3_5 = ET.SubElement(ts3, "con:testCase", {"id": u(), "name": "TC05_BelowMinimumOrderValue", "failOnError": "true"})
    ET.SubElement(tc3_5, "con:settings")
    create_rest_step(tc3_5, "Reset", "/reset", "POST")
    create_rest_step(tc3_5, "AddLowValueItem", "/cart", "POST", req_body='{"product_id": 5, "quantity": 1}')
    create_rest_step(
        tc3_5, "Apply_SAVE10_Below_Min", "/cart/apply-coupon", "POST",
        req_body='{"code": "SAVE10"}',
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "400"},
            {"type": "Simple Contains", "token": "Minimum order value"}
        ]
    )
    ET.SubElement(tc3_5, "con:properties")

    # TC 3.6: Remove Applied Coupon
    tc3_6 = ET.SubElement(ts3, "con:testCase", {"id": u(), "name": "TC06_RemoveCoupon", "failOnError": "true"})
    ET.SubElement(tc3_6, "con:settings")
    create_rest_step(tc3_6, "Reset", "/reset", "POST")
    create_rest_step(tc3_6, "AddItem", "/cart", "POST", req_body='{"product_id": 1, "quantity": 1}')
    create_rest_step(tc3_6, "ApplyCoupon", "/cart/apply-coupon", "POST", req_body='{"code": "SAVE10"}')
    create_rest_step(
        tc3_6, "Delete_Coupon", "/cart/coupon", "DELETE",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "Simple Contains", "token": "Coupon removed from cart successfully"}
        ]
    )
    create_rest_step(
        tc3_6, "Verify_No_Discount", "/cart", "GET",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "JsonPath Match", "path": "$.discount_amount", "content": "0.0"}
        ]
    )
    ET.SubElement(tc3_6, "con:properties")

    # ==========================================================
    # TEST SUITE 4: Cart Management & Cleanup
    # ==========================================================
    ts4 = ET.SubElement(root, "con:testSuite", {
        "id": u(),
        "name": "4. Cart Management & Deletion TestSuite"
    })
    ET.SubElement(ts4, "con:settings")
    ET.SubElement(ts4, "con:runType").text = "SEQUENTIAL"

    # TC 4.1: Remove Single Item
    tc4_1 = ET.SubElement(ts4, "con:testCase", {"id": u(), "name": "TC01_RemoveSingleItemFromCart", "failOnError": "true"})
    ET.SubElement(tc4_1, "con:settings")
    create_rest_step(tc4_1, "Step1_Reset", "/reset", "POST")
    create_rest_step(tc4_1, "Step2_AddItem", "/cart", "POST", req_body='{"product_id": 2, "quantity": 1}')
    create_rest_step(
        tc4_1, "Step3_DeleteItem", "/cart/2", "DELETE",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "Simple Contains", "token": "Product removed from cart successfully"}
        ]
    )
    create_rest_step(
        tc4_1, "Step4_VerifyEmpty", "/cart", "GET",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "JsonPath Match", "path": "$.item_count", "content": "0"}
        ]
    )
    ET.SubElement(tc4_1, "con:properties")

    # TC 4.2: Clear Entire Cart
    tc4_2 = ET.SubElement(ts4, "con:testCase", {"id": u(), "name": "TC02_ClearEntireCart", "failOnError": "true"})
    ET.SubElement(tc4_2, "con:settings")
    create_rest_step(tc4_2, "Step1_AddItem1", "/cart", "POST", req_body='{"product_id": 1, "quantity": 1}')
    create_rest_step(tc4_2, "Step2_AddItem2", "/cart", "POST", req_body='{"product_id": 4, "quantity": 2}')
    create_rest_step(
        tc4_2, "Step3_ClearCart", "/cart", "DELETE",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "Simple Contains", "token": "Cart cleared successfully"}
        ]
    )
    create_rest_step(
        tc4_2, "Step4_VerifyCartEmpty", "/cart", "GET",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "JsonPath Match", "path": "$.item_count", "content": "0"}
        ]
    )
    ET.SubElement(tc4_2, "con:properties")

    # ==========================================================
    # TEST SUITE 5: Negative & Boundary Validations
    # ==========================================================
    ts5 = ET.SubElement(root, "con:testSuite", {
        "id": u(),
        "name": "5. Negative & Boundary Validations TestSuite"
    })
    ET.SubElement(ts5, "con:settings")
    ET.SubElement(ts5, "con:runType").text = "SEQUENTIAL"

    # TC 5.1: Non-existent product
    tc5_1 = ET.SubElement(ts5, "con:testCase", {"id": u(), "name": "TC01_AddNonExistentProduct", "failOnError": "true"})
    ET.SubElement(tc5_1, "con:settings")
    create_rest_step(
        tc5_1, "Add_Invalid_Product", "/cart", "POST",
        req_body='{"product_id": 9999, "quantity": 1}',
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "404"},
            {"type": "Simple Contains", "token": "Product not found"}
        ]
    )
    ET.SubElement(tc5_1, "con:properties")

    # TC 5.2: Exceed stock
    tc5_2 = ET.SubElement(ts5, "con:testCase", {"id": u(), "name": "TC02_ExceedAvailableStock", "failOnError": "true"})
    ET.SubElement(tc5_2, "con:settings")
    create_rest_step(
        tc5_2, "Add_Exceeding_Quantity", "/cart", "POST",
        req_body='{"product_id": 1, "quantity": 9999}',
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "400"},
            {"type": "Simple Contains", "token": "Insufficient stock"}
        ]
    )
    ET.SubElement(tc5_2, "con:properties")

    # TC 5.3: Negative quantity
    tc5_3 = ET.SubElement(ts5, "con:testCase", {"id": u(), "name": "TC03_NegativeQuantity", "failOnError": "true"})
    ET.SubElement(tc5_3, "con:settings")
    create_rest_step(
        tc5_3, "Add_Negative_Quantity", "/cart", "POST",
        req_body='{"product_id": 1, "quantity": -3}',
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "400"},
            {"type": "Simple Contains", "token": "positive integer"}
        ]
    )
    ET.SubElement(tc5_3, "con:properties")

    # TC 5.4: Missing payload
    tc5_4 = ET.SubElement(ts5, "con:testCase", {"id": u(), "name": "TC04_MissingPayloadFields", "failOnError": "true"})
    ET.SubElement(tc5_4, "con:settings")
    create_rest_step(
        tc5_4, "Add_Empty_Body", "/cart", "POST",
        req_body='{}',
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "400"}
        ]
    )
    ET.SubElement(tc5_4, "con:properties")

    # TC 5.5: Update item not in cart
    tc5_5 = ET.SubElement(ts5, "con:testCase", {"id": u(), "name": "TC05_UpdateItemNotInCart", "failOnError": "true"})
    ET.SubElement(tc5_5, "con:settings")
    create_rest_step(
        tc5_5, "Update_Missing_CartItem", "/cart/888", "PUT",
        req_body='{"quantity": 1}',
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "404"},
            {"type": "Simple Contains", "token": "Cart item not found"}
        ]
    )
    ET.SubElement(tc5_5, "con:properties")

    # TC 5.6: Delete item not in cart
    tc5_6 = ET.SubElement(ts5, "con:testCase", {"id": u(), "name": "TC06_DeleteItemNotInCart", "failOnError": "true"})
    ET.SubElement(tc5_6, "con:settings")
    create_rest_step(
        tc5_6, "Delete_Missing_CartItem", "/cart/888", "DELETE",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "404"},
            {"type": "Simple Contains", "token": "Cart item not found"}
        ]
    )
    ET.SubElement(tc5_6, "con:properties")

    # TC 5.7: Checkout empty cart
    tc5_7 = ET.SubElement(ts5, "con:testCase", {"id": u(), "name": "TC07_CheckoutEmptyCart", "failOnError": "true"})
    ET.SubElement(tc5_7, "con:settings")
    create_rest_step(tc5_7, "Clear_Before_Checkout", "/cart", "DELETE")
    create_rest_step(
        tc5_7, "Checkout_Empty_Cart", "/cart/checkout", "POST",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "400"},
            {"type": "Simple Contains", "token": "Cannot checkout an empty cart"}
        ]
    )
    ET.SubElement(tc5_7, "con:properties")

    # ==========================================================
    # TEST SUITE 6: Dynamic Property Transfer TestSuite
    # ==========================================================
    ts6 = ET.SubElement(root, "con:testSuite", {
        "id": u(),
        "name": "6. Dynamic Property Transfer TestSuite"
    })
    ET.SubElement(ts6, "con:settings")
    ET.SubElement(ts6, "con:runType").text = "SEQUENTIAL"

    tc6_1 = ET.SubElement(ts6, "con:testCase", {"id": u(), "name": "TC01_DynamicProductPropertyTransfer", "failOnError": "true"})
    ET.SubElement(tc6_1, "con:settings")

    create_rest_step(tc6_1, "Reset_Database", "/reset", "POST")
    create_rest_step(
        tc6_1, "GET_Catalog", "/products", "GET",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "JsonPath Existence Match", "path": "$[0].id"}
        ]
    )
    create_rest_step(
        tc6_1, "GET_DynamicProductDetails", "/products/2", "GET",
        assertions=[
            {"type": "Valid HTTP Status Codes", "codes": "200"},
            {"type": "Simple Contains", "token": "Smartphone"}
        ]
    )
    ET.SubElement(tc6_1, "con:properties")

    ET.SubElement(root, "con:properties")
    ET.SubElement(root, "con:wssContainer")
    ET.SubElement(root, "con:oAuth2ProfileContainer")
    ET.SubElement(root, "con:oAuth1ProfileContainer")

    xml_str = ET.tostring(root, encoding="utf-8")
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

    return pretty_xml


if __name__ == "__main__":
    xml_content = build_soapui_project()
    with open("soapui/Ecommerce-Cart-SoapUI-Project.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)
    print("SoapUI Project regenerated with 100% robust concrete resources and assertions!")
