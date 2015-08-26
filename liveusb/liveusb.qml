import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2

import LiveUSB 1.0

import "components"

ApplicationWindow {
    id: mainWindow
    minimumWidth: $(800)
    minimumHeight: $(480)
    width: $(800)
    height: $(480)
    title: qsTranslate("", "Fedora LiveUSB Creator")

    SystemPalette {
        id: palette
    }

    property real scalingFactor: Math.ceil(Screen.pixelDensity * 25.4) / 96
    function $(x) {
        return x * scalingFactor
    }

    property bool canGoBack: false
    property real margin: $(64) + (width - $(800)) / 4

    Rectangle {
        anchors.fill: parent
        color: palette.window
        //radius: 8
        clip: true

        ListView {
            id: contentList
            anchors{
                top: parent.top
                bottom: parent.bottom
                left: parent.left
                right: parent.right
            }
            model: ["components/ImageList.qml", "components/ImageDetails.qml"]
            orientation: ListView.Horizontal
            snapMode: ListView.SnapToItem
            highlightFollowsCurrentItem: true
            highlightRangeMode: ListView.StrictlyEnforceRange
            interactive: false
            highlightMoveVelocity: 3 * contentList.width
            highlightResizeDuration: 0
            cacheBuffer: 2*width
            delegate: Item {
                id: contentComponent
                width: contentList.width
                height: contentList.height
                Loader {
                    id: contentLoader
                    source: contentList.model[index]
                    anchors.fill: parent
                }
                Connections {
                    target: contentLoader.item
                    onStepForward: {
                        liveUSBData.currentIndex = index
                        contentList.currentIndex = 1
                        canGoBack = true
                    }
                }
            }
        }
    }
}

