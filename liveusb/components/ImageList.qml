import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Layouts 1.1

Item {
    id: root

    property alias currentIndex: osListView.currentIndex
    property real fadeDuration: 200

    signal stepForward(int index)

    anchors.fill: parent
    clip: true

    Rectangle {
        enabled: !liveUSBData.releaseProxyModel.isFront
        opacity: !liveUSBData.releaseProxyModel.isFront ? 1.0 : 0.0
        id: searchBox
        border {
            color: searchInput.activeFocus ? "#4a90d9" : "#c3c3c3"
            width: 1
        }
        radius: $(6)
        color: "white"
        anchors {
            top: parent.top
            left: parent.left
            right: archSelect.left
            topMargin: $(12)
            leftMargin: mainWindow.margin
            rightMargin: $(4)
        }
        height: $(36)

        Item {
            id: magnifyingGlass
            anchors {
                left: parent.left
                leftMargin: (parent.height - height) / 2
                verticalCenter: parent.verticalCenter
            }
            height: childrenRect.height + $(3)
            width: childrenRect.width + $(2)

            Rectangle {
                height: $(11)
                antialiasing: true
                width: height
                radius: height / 2
                color: "black"
                Rectangle {
                    height: $(7)
                    antialiasing: true
                    width: height
                    radius: height / 2
                    color: "white"
                    anchors.centerIn: parent
                }
                Rectangle {
                    height: $(2)
                    width: $(6)
                    radius: $(2)
                    x: $(8)
                    y: $(11)
                    rotation: 45
                    color: "black"
                }
            }
        }
        TextInput {
            id: searchInput
            anchors {
                left: magnifyingGlass.right
                top: parent.top
                bottom: parent.bottom
                right: parent.right
                margins: $(8)
            }
            Text {
                anchors.fill: parent
                color: "light gray"
                font.pointSize: $(9)
                text: qsTranslate("", "Find an operating system image")
                visible: !parent.activeFocus && parent.text.length == 0
                verticalAlignment: Text.AlignVCenter
            }
            verticalAlignment: TextInput.AlignVCenter
            text: liveUSBData.releaseProxyModel.nameFilter
            onTextChanged: liveUSBData.releaseProxyModel.nameFilter = text
            clip: true
        }
    }

    AdwaitaComboBox {
        enabled: !liveUSBData.releaseProxyModel.isFront
        opacity: !liveUSBData.releaseProxyModel.isFront ? 1.0 : 0.0
        Behavior on opacity {
            NumberAnimation {
                duration: root.fadeDuration
            }
        }

        id: archSelect
        anchors {
            right: parent.right
            top: parent.top
            rightMargin: mainWindow.margin
            topMargin: $(12)
        }
        height: $(36)
        width: $(148)
        model: liveUSBData.releaseProxyModel.possibleArchs
        onCurrentIndexChanged:  {
            liveUSBData.releaseProxyModel.archFilter = currentText
        }
        function update() {
            for (var i = 0; i < liveUSBData.releaseProxyModel.possibleArchs.length; i++) {
                if (liveUSBData.releaseProxyModel.possibleArchs[i] == liveUSBData.releaseProxyModel.archFilter)
                    currentIndex = i
            }
        }

        Connections {
            target: liveUSBData.releaseProxyModel
            onArchFilterChanged: archSelect.update()
        }
        Component.onCompleted: update()
    }

    Rectangle {
        id: whiteBackground
        z: -1
        clip: true
        radius: $(6)
        color: "white"
        y: liveUSBData.releaseProxyModel.isFront || moveUp.running ? parent.height / 2 - height / 2 : $(54)
        Behavior on y {
            id: moveUp
            enabled: false

            NumberAnimation {
                onStopped: moveUp.enabled = false
            }
        }

        //height: !liveUSBData.releaseProxyModel.isFront ? parent.height - 54 + 4 : parent.height - 108
        height: liveUSBData.releaseProxyModel.isFront ? $(84) * 3 + $(36) : parent.height

        /*Behavior on height {
            NumberAnimation { duration: root.fadeDuration }
        }*/
        anchors {
            left: parent.left
            right: parent.right
            rightMargin: mainWindow.margin
            leftMargin: anchors.rightMargin
        }
        border {
            color: "#c3c3c3"
            width: 1
        }
    }

    ScrollView {
        id: fullList
        anchors.fill: parent
        ListView {
            id: osListView
            clip: true
            anchors {
                fill: parent
                leftMargin: mainWindow.margin
                rightMargin: anchors.leftMargin - (fullList.width - fullList.viewport.width)
                topMargin: whiteBackground.y
            }
            footer: Item {
                height: !liveUSBData.releaseProxyModel.isFront ? $(54) : $(36)
                width: osListView.width
                Rectangle {
                    clip: true
                    visible: liveUSBData.releaseProxyModel.isFront
                    anchors.fill: parent
                    anchors.margins: 1
                    radius: 3
                    Column {
                        id: threeDotDots
                        property bool hidden: false
                        opacity: hidden ? 0.0 : 1.0
                        Behavior on opacity { NumberAnimation { duration: 60 } }
                        anchors.centerIn: parent
                        spacing: 2
                        Repeater {
                            model: 3
                            Rectangle {
                                height: $(4)
                                width: $(4)
                                color: "#bebebe"
                            }
                        }
                    }
                    Text {
                        id: threeDotText
                        y: threeDotDots.hidden ? parent.height / 2 - height / 2 : -height
                        font.pointSize: $(9)
                        anchors.horizontalCenter: threeDotDots.horizontalCenter
                        Behavior on y { NumberAnimation { duration: 60 } }
                        clip: true
                        text: qsTranslate("", "Display additional Fedora flavors")
                        color: "gray"
                    }
                    Timer {
                        id: threeDotTimer
                        interval: 200
                        onTriggered: {
                            threeDotDots.hidden = true
                        }
                    }
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onHoveredChanged: {
                            if (containsMouse && !pressed) {
                                parent.color = "#f8f8f8"
                                threeDotTimer.start()
                            }
                            if (!containsMouse) {
                                parent.color = "transparent"
                                threeDotTimer.stop()
                                threeDotDots.hidden = false
                            }
                        }
                        onClicked: {
                            moveUp.enabled = true
                            liveUSBData.releaseProxyModel.isFront = false
                        }
                        onPressed: {
                            parent.color = "#ededed"
                        }
                        onReleased: {
                            parent.color = "transparent"
                        }
                        onCanceled: {
                            parent.color = "transparent"
                        }
                    }
                }
            }

            model: liveUSBData.releaseProxyModel
            delegate: imageDelegate

            remove: Transition {
                NumberAnimation { properties: "x"; to: width; duration: 300 }
            }
            removeDisplaced: Transition {
                NumberAnimation { properties: "x,y"; duration: 300 }
            }
            add: Transition {
                NumberAnimation { properties: liveUSBData.releaseProxyModel.isFront ? "y" : "x"; from: liveUSBData.releaseProxyModel.isFront ? 0 : -width; duration: 300 }
            }
            addDisplaced: Transition {
                NumberAnimation { properties: "x,y"; duration: 300 }
            }
        }
        style: ScrollViewStyle {
            incrementControl: Item {}
            decrementControl: Item {}
            corner: Item {
                implicitWidth: $(11)
                implicitHeight: $(11)
            }
            scrollBarBackground: Rectangle {
                color: "#dddddd"
                implicitWidth: $(11)
                implicitHeight: $(11)
            }
            handle: Rectangle {
                color: "#b3b5b6"
                x: $(2)
                y: $(2)
                implicitWidth: $(7)
                implicitHeight: $(7)
                radius: $(4)
            }
            transientScrollBars: false
            handleOverlap: $(1)
            minimumHandleLength: $(10)
        }
    }

    Component {
        id: imageDelegate
        Item {
            width: parent.width
            height: $(84)
            Rectangle {
                width: parent.width - 2
                height: index == 0 ? parent.height - 1 : parent.height
                x: 1
                y: index == 0 ? 1 : 0
                radius: $(4)
                color: "transparent"
                IndicatedImage {
                    id: iconRect
                    anchors {
                        top: parent.top
                        left: parent.left
                        bottom: parent.bottom
                        leftMargin: $(32)
                        topMargin: $(16)
                        bottomMargin: anchors.topMargin
                    }
                    width: height
                    smooth: true
                    fillMode: Image.PreserveAspectFit

                    source: release.logo
                }
                Item {
                    id: textRect
                    anchors {
                        verticalCenter: parent.verticalCenter
                        left: iconRect.right
                        right: arrow.left
                        bottom: parent.bottom
                        leftMargin: $(28)
                        rightMargin: $(14)
                    }
                    Text {
                        font.pointSize: $(9)
                        text: release.name
                        anchors {
                            bottom: parent.verticalCenter
                            left: parent.left
                            bottomMargin: $(2)
                        }
                        // font.weight: Font.Bold
                    }
                    Text {
                        font.pointSize: $(9)
                        text: release.summary
                        anchors {
                            top: parent.verticalCenter
                            left: parent.left
                            right: parent.right
                            topMargin: $(2)
                        }
                        wrapMode: Text.Wrap
                        color: "#a1a1a1"
                        // font.weight: Font.Bold
                    }
                }
                Arrow {
                    id: arrow
                    visible: !release.isLocal
                    scale: $(1)
                    anchors {
                        verticalCenter: parent.verticalCenter
                        right: parent.right
                        rightMargin: $(20)
                    }
                }
                Rectangle {
                    height: 1
                    color: "#c3c3c3"
                    width: parent.width
                    anchors.bottom: parent.bottom
                }
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onHoveredChanged: {
                        if (containsMouse && !pressed)
                            parent.color = "#f8f8f8"
                        if (!containsMouse)
                            parent.color = "transparent"
                    }
                    onClicked: {
                        root.currentIndex = index
                        root.stepForward(release.index)
                    }
                    onPressed: {
                        parent.color = "#ededed"
                    }
                    onReleased: {
                        parent.color = "transparent"
                    }
                    onCanceled: {
                        parent.color = "transparent"
                    }
                }
            }
        }
    }
}
