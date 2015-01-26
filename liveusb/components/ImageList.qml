import QtQuick 2.4

Rectangle {
    id: root

    property alias currentIndex: osListView.currentIndex
    signal triggered

    clip: true
    border {
        color: "#c3c3c3"
        width: 1
    }
    radius: 6
    color: "white"
    ListView {
        id: osListView
        clip: true
        anchors.fill: parent
        model: osList
        delegate: Rectangle {
            width: parent.width - 2
            height: 84
            x: 1
            y: 1
            color: "transparent"
            Rectangle {
                id: iconRect
                anchors {
                    top: parent.top
                    left: parent.left
                    bottom: parent.bottom
                    leftMargin: 32
                    topMargin: 16
                    bottomMargin: anchors.topMargin
                }
                width: height

                color: "transparent"
                border.color: "#c3c3c3"
                border.width: 1
            }
            Item {
                id: textRect
                anchors {
                    verticalCenter: parent.verticalCenter
                    left: iconRect.right
                    leftMargin: 28
                }
                Text {
                    text: name
                    anchors {
                        bottom: parent.verticalCenter
                        left: parent.left
                        bottomMargin: 2
                    }
                    font.weight: Font.Bold
                }
                Text {
                    text: description
                    anchors {
                        top: parent.verticalCenter
                        left: parent.right
                        topMargin: 2
                    }
                    color: "#a1a1a1"
                    font.weight: Font.Bold
                }
            }
            Arrow {
                visible: hasDetails
                anchors {
                    verticalCenter: parent.verticalCenter
                    right: parent.right
                    rightMargin: 20
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
                onClicked: {
                    root.currentIndex = index
                    root.triggered()
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
