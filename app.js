"use strict";

/* =========================
   STATE
========================= */

const state = {
    weapons: [],
    filtered: [],
    category: "すべて",
    selected: null
};


/* =========================
   HELPERS
========================= */

const $ = (selector) => {
    return document.querySelector(selector);
};


function escapeHTML(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


function displayValue(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "—";
    }

    return value;

}


function toNumber(value) {

    const number = parseFloat(value);

    if (Number.isFinite(number)) {
        return number;
    }

    return null;

}


/* =========================
   DATA LOAD
========================= */

async function loadWeapons() {

    try {

        const response = await fetch(
            "data/weapons.json?" + Date.now(),
            {
                cache: "no-store"
            }
        );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        const data = await response.json();


        if (!Array.isArray(data)) {

            throw new Error(
                "weapons.jsonの形式が正しくありません"
            );

        }


        state.weapons = data;


        $("#dataStatus").textContent =
            `データ ${data.length}件`;


        createCategories();

        filterWeapons();


    } catch (error) {

        console.error(
            "武器データ読み込みエラー:",
            error
        );


        $("#dataStatus").textContent =
            "データ読み込み失敗";


        $("#weaponList").innerHTML = `

            <div class="note">

                weapons.jsonを読み込めません。

                <br><br>

                GitHub上の

                <strong>
                    data/weapons.json
                </strong>

                が存在するか確認してください。

            </div>

        `;

    }

}


/* =========================
   CATEGORY
========================= */

function createCategories() {

    const categories = [

        "すべて",

        ...new Set(

            state.weapons

                .map(
                    weapon => weapon.category
                )

                .filter(Boolean)

        )

    ];


    $("#categories").innerHTML =

        categories.map(category => {

            const active =
                category === state.category
                    ? "active"
                    : "";


            return `

                <button
                    class="
                        category-button
                        ${active}
                    "
                    data-category="${escapeHTML(category)}"
                >

                    ${escapeHTML(category)}

                </button>

            `;

        }).join("");


    document
        .querySelectorAll(".category-button")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    state.category =
                        button.dataset.category;


                    createCategories();

                    filterWeapons();

                }
            );

        });

}


/* =========================
   FILTER
========================= */

function filterWeapons() {

    const input =
        $("#search");

    const query =
        input
            ? input.value
                .trim()
                .toLowerCase()
            : "";


    state.filtered =
        state.weapons.filter(weapon => {


            const categoryOK =

                state.category === "すべて"

                ||

                weapon.category ===
                state.category;


            const searchableText = `

                ${weapon.name || ""}

                ${weapon.sub || ""}

                ${weapon.special || ""}

            `.toLowerCase();


            const searchOK =

                query === ""

                ||

                searchableText.includes(
                    query
                );


            return (
                categoryOK &&
                searchOK
            );

        });


    $("#weaponCount").textContent =
        state.filtered.length;


    $("#weaponList").innerHTML =

        state.filtered.map(weapon => {


            const active =

                state.selected &&
                state.selected.id ===
                weapon.id

                    ? "active"

                    : "";


            return `

                <button
                    class="
                        weapon-button
                        ${active}
                    "
                    data-id="${escapeHTML(weapon.id)}"
                >

                    <div class="weapon-name">

                        ${escapeHTML(
                            displayValue(
                                weapon.name
                            )
                        )}

                    </div>


                    <div class="weapon-meta">

                        ${escapeHTML(
                            displayValue(
                                weapon.category
                            )
                        )}

                        　

                        射程

                        ${escapeHTML(
                            displayValue(
                                weapon.range
                            )
                        )}

                    </div>

                </button>

            `;

        }).join("");


    if (state.filtered.length === 0) {

        $("#weaponList").innerHTML = `

            <div class="note">

                該当するブキがありません。

            </div>

        `;

    }


    document
        .querySelectorAll(".weapon-button")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    selectWeapon(
                        button.dataset.id
                    );

                }
            );

        });

}


/* =========================
   SEARCH
========================= */

$("#search").addEventListener(
    "input",
    () => {

        filterWeapons();

    }
);


/* =========================
   WEAPON SELECT
========================= */

function selectWeapon(id) {

    state.selected =
        state.weapons.find(
            weapon =>
                weapon.id === id
        );


    if (!state.selected) {
        return;
    }


    filterWeapons();

    renderWeapon();

}


/* =========================
   RENDER WEAPON
========================= */

function renderWeapon() {

    const weapon =
        state.selected;


    if (!weapon) {
        return;
    }


    const range =
        toNumber(
            weapon.range
        );


    const paintRange =
        toNumber(
            weapon.paintRange
        );


    const blastRange =
        toNumber(
            weapon.blastRange
        );


    const blastRadius =
        toNumber(
            weapon.blastRadius
        );


    const graphMax =
        Math.max(
            5,
            range || 0,
            paintRange || 0,
            blastRange || 0
        ) * 1.1;


    $("#detail").innerHTML = `

        <div class="detail-grid">


            <!-- =====================
                 WEAPON HEADER
            ====================== -->

            <section
                class="
                    card
                    weapon-header
                "
            >

                <div class="weapon-category">

                    ${escapeHTML(
                        displayValue(
                            weapon.category
                        )
                    )}

                </div>


                <h2>

                    ${escapeHTML(
                        displayValue(
                            weapon.name
                        )
                    )}

                </h2>


                <div class="kit">

                    <span class="tag">

                        サブ：

                        ${escapeHTML(
                            displayValue(
                                weapon.sub
                            )
                        )}

                    </span>


                    <span class="tag">

                        スペシャル：

                        ${escapeHTML(
                            displayValue(
                                weapon.special
                            )
                        )}

                    </span>


                    <span class="tag">

                        必要P：

                        ${escapeHTML(
                            displayValue(
                                weapon.specialPoints
                            )
                        )}

                    </span>

                </div>


                <div class="source">

                    参照：

                    ${
                        weapon.wikiUrl
                            ? `

                                <a
                                    href="${escapeHTML(
                                        weapon.wikiUrl
                                    )}"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >

                                    WikiWiki

                                </a>

                            `
                            : ""
                    }


                    ${
                        weapon.inkipediaUrl
                            ? `

                                /

                                <a
                                    href="${escapeHTML(
                                        weapon.inkipediaUrl
                                    )}"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >

                                    Inkipedia

                                </a>

                            `
                            : ""
                    }

                </div>

            </section>


            <!-- =====================
                 RANGE
            ====================== -->

            <section class="card">

                <h3 class="section-title">

                    射程

                </h3>


                <div class="range-area">

                    <div class="range-axis">


                        ${
                            range !== null

                                ?

                            `

                                <div
                                    class="range-bar"
                                    style="
                                        width:
                                        ${
                                            range /
                                            graphMax *
                                            100
                                        }%;
                                    "
                                ></div>


                                <div
                                    class="range-marker"
                                    style="
                                        left:
                                        ${
                                            range /
                                            graphMax *
                                            100
                                        }%;
                                    "
                                ></div>


                                <div
                                    class="range-label"
                                    style="
                                        left:
                                        ${
                                            range /
                                            graphMax *
                                            100
                                        }%;
                                    "
                                >

                                    有効
                                    ${range}

                                </div>

                            `

                                :

                            ""

                        }


                        ${
                            paintRange !== null

                                ?

                            `

                                <div
                                    class="range-marker"
                                    style="
                                        left:
                                        ${
                                            paintRange /
                                            graphMax *
                                            100
                                        }%;

                                        height:20px;

                                        background:#888;
                                    "
                                ></div>


                                <div
                                    class="range-label"
                                    style="
                                        left:
                                        ${
                                            paintRange /
                                            graphMax *
                                            100
                                        }%;

                                        bottom:-58px;

                                        color:#aaa;
                                    "
                                >

                                    塗り
                                    ${paintRange}

                                </div>

                            `

                                :

                            ""

                        }


                    </div>

                </div>

            </section>


            <!-- =====================
                 BASIC PERFORMANCE
            ====================== -->

            <section class="card">

                <h3 class="section-title">

                    基本性能

                </h3>


                <div class="stats">


                    ${createStat(
                        "最大ダメージ",
                        weapon.damageMax
                    )}


                    ${createStat(
                        "最小ダメージ",
                        weapon.damageMin
                    )}


                    ${createStat(
                        "確定数",
                        weapon.kills
                    )}


                    ${createStat(
                        "キル速",
                        weapon.killTime,
                        weapon.killTime !== null &&
                        weapon.killTime !== undefined &&
                        weapon.killTime !== ""
                            ? "秒"
                            : ""
                    )}


                    ${createStat(
                        "連射速度",
                        weapon.fireRate,
                        weapon.fireRate !== null &&
                        weapon.fireRate !== undefined &&
                        weapon.fireRate !== ""
                            ? "F"
                            : ""
                    )}


                    ${createStat(
                        "DPS",
                        weapon.dps
                    )}


                </div>

            </section>


            <!-- =====================
                 DAMAGE
            ====================== -->

            <section class="card">

                <h3 class="section-title">

                    ダメージ

                </h3>


                <div class="damage-list">


                    ${createDamageBar(
                        "最大",
                        toNumber(
                            weapon.damageMax
                        )
                    )}


                    ${createDamageBar(
                        "最小",
                        toNumber(
                            weapon.damageMin
                        )
                    )}


                    ${
                        weapon.directDamage !==
                        null &&
                        weapon.directDamage !==
                        undefined

                            ?

                        createDamageBar(
                            "直撃",
                            toNumber(
                                weapon.directDamage
                            )
                        )

                            :

                        ""
                    }


                    ${
                        weapon.blastDamage !==
                        null &&
                        weapon.blastDamage !==
                        undefined

                            ?

                        createDamageBar(
                            "爆風",
                            toNumber(
                                weapon.blastDamage
                            )
                        )

                            :

                        ""
                    }


                </div>

            </section>


            <!-- =====================
                 BLAST
            ====================== -->

            ${
                blastRange !== null ||
                blastRadius !== null

                    ?

                `

                    <section class="card">

                        <h3 class="section-title">

                            爆風範囲

                        </h3>


                        <div class="blast-area">


                            ${
                                blastRange !== null

                                    ?

                                `

                                    <div
                                        class="blast-line"
                                        style="
                                            width:
                                            ${
                                                blastRange /
                                                graphMax *
                                                100
                                            }%;
                                        "
                                    ></div>

                                `

                                    :

                                ""
                            }


                            ${
                                blastRadius !== null

                                    ?

                                `

                                    <div
                                        class="blast-circle"
                                        style="
                                            left:
                                            ${
                                                (
                                                    blastRange ||
                                                    range ||
                                                    0
                                                ) /
                                                graphMax *
                                                100
                                            }%;

                                            width:
                                            ${
                                                Math.max(
                                                    36,
                                                    blastRadius *
                                                    70
                                                )
                                            }px;

                                            height:
                                            ${
                                                Math.max(
                                                    36,
                                                    blastRadius *
                                                    70
                                                )
                                            }px;
                                        "
                                    ></div>

                                `

                                    :

                                ""
                            }


                            <div class="blast-caption">

                                爆風射程：
                                ${escapeHTML(
                                    displayValue(
                                        weapon.blastRange
                                    )
                                )}

                                　

                                爆風半径：
                                ${escapeHTML(
                                    displayValue(
                                        weapon.blastRadius
                                    )
                                )}

                            </div>


                        </div>

                    </section>

                `

                    :

                ""

            }


            <!-- =====================
                 FALLOFF
            ====================== -->

            <section class="card">

                <h3 class="section-title">

                    距離減衰

                </h3>


                <svg
                    class="chart"
                    viewBox="0 0 700 230"
                    preserveAspectRatio="none"
                >

                    ${createFalloffGraph(
                        weapon
                    )}

                </svg>


                <p class="note">

                    最大ダメージから最小ダメージまでを
                    視覚化しています。
                    Wikiから正確な減衰点を取得できない場合は
                    推測値を追加しません。

                </p>

            </section>


            <!-- =====================
                 OTHER DATA
            ====================== -->

            <section class="card">

                <h3 class="section-title">

                    その他

                </h3>


                <div class="spec-grid">


                    ${createSpec(
                        "有効射程",
                        weapon.range
                    )}


                    ${createSpec(
                        "確定数維持射程",
                        weapon.maintainRange
                    )}


                    ${createSpec(
                        "レティクル反応距離",
                        weapon.reticleRange
                    )}


                    ${createSpec(
                        "塗り射程",
                        weapon.paintRange
                    )}


                    ${createSpec(
                        "連射フレーム",
                        weapon.fireRate
                    )}


                    ${createSpec(
                        "秒間発射数",
                        weapon.shotsPerSecond
                    )}


                    ${createSpec(
                        "キルタイム",
                        weapon.killTime
                    )}


                    ${createSpec(
                        "DPS",
                        weapon.dps
                    )}


                    ${createSpec(
                        "爆風半径",
                        weapon.blastRadius
                    )}


                </div>

            </section>


        </div>

    `;

}


/* =========================
   STAT
========================= */

function createStat(
    label,
    value,
    suffix = ""
) {

    return `

        <div class="stat">

            <div class="stat-label">

                ${label}

            </div>


            <div class="stat-value">

                ${escapeHTML(
                    displayValue(value)
                )}

                ${suffix}

            </div>

        </div>

    `;

}


/* =========================
   SPEC
========================= */

function createSpec(
    label,
    value
) {

    return `

        <div class="spec">

            <b>

                ${label}

            </b>


            <span>

                ${escapeHTML(
                    displayValue(value)
                )}

            </span>

        </div>

    `;

}


/* =========================
   DAMAGE BAR
========================= */

function createDamageBar(
    label,
    damage
) {

    if (damage === null) {

        return "";

    }


    const percentage =

        Math.max(
            0,
            Math.min(
                100,
                damage / 120 * 100
            )
        );


    return `

        <div class="damage-row">

            <span>

                ${label}

            </span>


            <div class="damage-track">

                <div
                    class="damage-fill"
                    style="
                        width:
                        ${percentage}%;
                    "
                ></div>

            </div>


            <b>

                ${damage}

            </b>

        </div>

    `;

}


/* =========================
   FALLOFF GRAPH
========================= */

function createFalloffGraph(
    weapon
) {

    const max =
        toNumber(
            weapon.damageMax
        );


    const min =
        toNumber(
            weapon.damageMin
        );


    if (
        max === null ||
        min === null
    ) {

        return `

            <text
                x="55"
                y="55"
            >

                距離減衰データなし

            </text>

        `;

    }


    const x1 = 60;

    const x2 = 665;

    const yMax = 35;

    const yMin = 175;


    const start =
        weapon.damageStartFrame;


    const end =
        weapon.damageEndFrame;


    return `

        <line
            x1="45"
            y1="20"
            x2="45"
            y2="195"
            stroke="#555"
        ></line>


        <line
            x1="45"
            y1="195"
            x2="680"
            y2="195"
            stroke="#555"
        ></line>


        <polyline
            points="
                ${x1},${yMax}
                ${x2},${yMin}
            "
            fill="none"
            stroke="#fff"
            stroke-width="4"
        ></polyline>


        <circle
            cx="${x1}"
            cy="${yMax}"
            r="5"
            fill="#fff"
        ></circle>


        <circle
            cx="${x2}"
            cy="${yMin}"
            r="5"
            fill="#fff"
        ></circle>


        <text
            x="${x1 + 8}"
            y="${yMax - 8}"
        >

            ${max}

        </text>


        <text
            x="${x2 - 25}"
            y="${yMin - 8}"
        >

            ${min}

        </text>


        <text
            x="${x1}"
            y="218"
        >

            ${
                start !== null &&
                start !== undefined
                    ? `${start}F`
                    : "開始"
            }

        </text>


        <text
            x="${x2 - 30}"
            y="218"
        >

            ${
                end !== null &&
                end !== undefined
                    ? `${end}F`
                    : "終端"
            }

        </text>

    `;

}


/* =========================
   START
========================= */

loadWeapons();
