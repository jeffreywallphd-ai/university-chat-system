import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            HomeView()
            ScheduleView()
            MapView()
            CareerFairView()
            CommonLinksView()
        }
    }
}
